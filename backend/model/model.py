import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['figure.dpi'] = 120

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except (ImportError, Exception) as e:
    XGBOOST_AVAILABLE = False
    print(f"XGBoost not available — install with: pip install xgboost (Error: {e})")

import os
import joblib
import json
import time

SEED = 42
np.random.seed(SEED)
print("All imports successful ✓")

base_dir = os.path.dirname(os.path.abspath(__file__))
train_path = os.path.join(base_dir, "Training.csv")

train_df = pd.read_csv(train_path)
test_df  = pd.read_csv(train_path)

# Drop unnamed/trailing columns from CSV export
train_df = train_df.loc[:, ~train_df.columns.str.startswith('Unnamed')]
test_df  = test_df.loc[:,  ~test_df.columns.str.startswith('Unnamed')]

print(f"Train shape : {train_df.shape}")
print(f"Test  shape : {test_df.shape}")
print(f"Diseases    : {train_df['prognosis'].nunique()}")
print("\nClass distribution (train):")
print(train_df['prognosis'].value_counts())
symptom_cols = [c for c in train_df.columns if c != 'prognosis']

X_train = train_df[symptom_cols].values
X_test  = test_df[symptom_cols].values

label_encoder = LabelEncoder()
label_encoder.fit(train_df['prognosis'])          # fit ONLY on train

y_train = label_encoder.transform(train_df['prognosis'])
y_test  = label_encoder.transform(test_df['prognosis'])

id2label = dict(enumerate(label_encoder.classes_))
num_classes = len(id2label)

print(f"Features  : {len(symptom_cols)} symptom columns")
print(f"Classes   : {num_classes} diseases")
print(f"Train rows: {len(X_train)}")
print(f"Test  rows: {len(X_test)}")
X_tr, X_val, y_tr, y_val = train_test_split(
    X_train, y_train,
    test_size=0.15,
    stratify=y_train,
    random_state=SEED,
)
print(f"Training   : {len(X_tr)} samples")
print(f"Validation : {len(X_val)} samples")
print(f"Test (held): {len(X_test)} samples")

models = {
    "Random Forest"       : RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
    "Gradient Boosting"   : GradientBoostingClassifier(n_estimators=150, random_state=SEED),
    "Logistic Regression" : LogisticRegression(max_iter=1000, random_state=SEED),
    "SVM (RBF)"           : SVC(kernel='rbf', probability=True, random_state=SEED),
}
if XGBOOST_AVAILABLE:
    models["XGBoost"] = XGBClassifier(
        n_estimators=150, use_label_encoder=False,
        eval_metric='mlogloss', random_state=SEED, n_jobs=-1
    )

rows = []
for name, clf in models.items():
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    elapsed = time.time() - t0

    val_acc  = accuracy_score(y_val,  clf.predict(X_val))
    test_acc = accuracy_score(y_test, clf.predict(X_test))
    rows.append({"Model": name, "Val Acc": val_acc, "Test Acc": test_acc, "Time (s)": round(elapsed, 2)})
    print(f"[{name:<22}]  val={val_acc:.4f}  test={test_acc:.4f}  ({elapsed:.1f}s)")

print()
results_df = pd.DataFrame(rows).sort_values("Test Acc", ascending=False)
print(results_df.to_string(index=False))    
best_model = RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1)
best_model.fit(X_train, y_train)       # full training set, no val split

y_pred = best_model.predict(X_test)
final_acc = accuracy_score(y_test, y_pred)

print(f"Final Test Accuracy: {final_acc:.4f}  ({final_acc*100:.2f}%)")
print()
print("=" * 65)
print("CLASSIFICATION REPORT")
print("=" * 65)
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(16, 14))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=label_encoder.classes_)
disp.plot(ax=ax, xticks_rotation=90, colorbar=False, cmap='Blues')
ax.set_title("Random Forest — Confusion Matrix (Test Set)", fontsize=13)
plt.tight_layout()
plt.close()  # Don't show in non-interactive mode

importances = best_model.feature_importances_
top_idx = np.argsort(importances)[::-1][:20]

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(range(20), importances[top_idx] * 100, color='coral')
ax.set_xticks(range(20))
ax.set_xticklabels([symptom_cols[i] for i in top_idx], rotation=45, ha='right', fontsize=9)
ax.set_ylabel("Importance (%)")
ax.set_title("Top 20 Most Predictive Symptoms")
plt.tight_layout()
plt.close()  # Don't show in non-interactive mode

cv_scores = cross_val_score(
    RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1),
    X_train, y_train,
    cv=5, scoring='accuracy', n_jobs=-1
)
print("5-Fold CV Accuracy per fold:", np.round(cv_scores, 4))
print(f"Mean ± Std : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")   

def predict_disease(symptom_list: list, verbose: bool = True) -> str:
    """
    Predict disease from a list of symptom names.
    
    Parameters
    ----------
    symptom_list : list of str
        Active symptom names, e.g. ['itching', 'skin_rash']
    verbose : bool
        Print formatted output (default True)
    
    Returns
    -------
    str — predicted disease name
    """
    # Build binary feature vector
    vec = np.zeros(len(symptom_cols), dtype=int)
    unknown = []
    for sym in symptom_list:
        sym_clean = sym.strip().lower().replace(' ', '_')
        if sym_clean in symptom_cols:
            vec[symptom_cols.index(sym_clean)] = 1
        else:
            unknown.append(sym)

    proba    = best_model.predict_proba([vec])[0]
    pred_id  = np.argmax(proba)
    disease  = id2label[pred_id]
    conf     = proba[pred_id]

    # Top-3 candidates
    top3_idx = np.argsort(proba)[::-1][:3]
    top3     = [(id2label[i], proba[i]) for i in top3_idx]

    if verbose:
        print(f"  Symptoms     : {symptom_list}")
        if unknown:
            print(f"  ⚠ Unknown symptoms (ignored): {unknown}")
        print(f"  Prediction   : {disease}")
        print(f"  Confidence   : {conf:.1%}")
        print(f"  Top-3        : {top3[0][0]} ({top3[0][1]:.1%}), "
              f"{top3[1][0]} ({top3[1][1]:.1%}), "
              f"{top3[2][0]} ({top3[2][1]:.1%})")
    return disease

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(base_dir), "app", "ml_models")
    os.makedirs(out_dir, exist_ok=True)
    
    print("\nSaving models to:", out_dir)
    joblib.dump(best_model, os.path.join(out_dir, "best_model.joblib"))
    joblib.dump(label_encoder, os.path.join(out_dir, "label_encoder.joblib"))
    with open(os.path.join(out_dir, "symptom_cols.json"), "w") as f:
        json.dump(symptom_cols, f)
    print("Saved artifacts successfully! ✓")