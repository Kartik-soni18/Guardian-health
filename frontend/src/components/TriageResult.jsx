import React from 'react';

const listStyle = {
  paddingLeft: '1.2rem',
  fontSize: '0.95rem',
  color: '#cbd5e1',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.5rem',
};

const ExternalLinkIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
    <polyline points="15 3 21 3 21 9"/>
    <line x1="10" y1="14" x2="21" y2="3"/>
  </svg>
);

const CareList = ({ title, items }) => {
  if (!items || items.length === 0) return null;
  return (
    <div className="triage-card">
      <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#f1f5f9' }}>{title}</h3>
      <ul style={listStyle}>
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  );
};

const OtcProducts = ({ products }) => {
  if (!products || products.length === 0) return null;
  return (
    <div className="triage-card">
      <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#f1f5f9' }}>🛒 Remedies & Products</h3>
      <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
        Common OTC items that may help — tap to search on Blinkit
      </p>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {products.map((product, i) => (
          <a
            key={i}
            href={`https://blinkit.com/s/?q=${encodeURIComponent(product)}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: 'rgba(251, 191, 36, 0.1)',
              border: '1px solid rgba(251, 191, 36, 0.35)',
              borderRadius: '8px',
              padding: '0.4rem 0.85rem',
              fontSize: '0.85rem',
              color: '#fde68a',
              textDecoration: 'none',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(251,191,36,0.2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(251,191,36,0.1)'}
          >
            <ExternalLinkIcon />
            {product}
          </a>
        ))}
      </div>
    </div>
  );
};

const Disclaimer = ({ text }) => (
  <div style={{
    padding: '1rem',
    background: 'rgba(0,0,0,0.3)',
    borderRadius: '12px',
    fontSize: '0.85rem',
    lineHeight: '1.5',
    color: '#fca5a5',
    border: '1px solid rgba(239, 68, 68, 0.2)',
  }}>
    ⚠️ {text}
  </div>
);

const TriageResult = ({ triage, disease, care, symptoms, severity }) => {
  if (!triage && !disease) return null;

  if (disease) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="triage-card" style={{ borderLeft: '4px solid #3b82f6' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.75rem', margin: 0, color: '#f1f5f9' }}>{disease.name}</h2>
            {disease.confidence != null && (
              <div style={{
                background: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid rgba(59, 130, 246, 0.4)',
                borderRadius: '8px',
                padding: '0.5rem 1rem',
                textAlign: 'center',
              }}>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase' }}>Confidence</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#60a5fa' }}>{disease.confidence_pct}</div>
              </div>
            )}
          </div>

          {disease.confidence != null && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ height: '8px', background: 'rgba(148, 163, 184, 0.3)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  background: 'linear-gradient(to right, #60a5fa, #3b82f6)',
                  width: `${Math.min(disease.confidence * 100, 100)}%`,
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          )}

          {symptoms && symptoms.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Your Reported Symptoms
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {symptoms.map((symptom, i) => (
                  <span key={i} style={{
                    background: 'rgba(59, 130, 246, 0.15)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: '6px',
                    padding: '0.35rem 0.75rem',
                    fontSize: '0.85rem',
                    color: '#e0f2fe',
                  }}>
                    {symptom}
                  </span>
                ))}
              </div>
            </div>
          )}

          {severity && (
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', marginBottom: '0.5rem' }}>
              <strong>Severity:</strong> {severity}
            </p>
          )}
        </div>

        {disease.all_predictions && disease.all_predictions.length > 0 && (
          <div className="triage-card">
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#f1f5f9' }}>Top Diagnostic Possibilities</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {disease.all_predictions.map(([name, confidence], idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ color: '#94a3b8', minWidth: '120px' }}>{name}</span>
                  <div style={{ flex: 1, height: '6px', background: 'rgba(148, 163, 184, 0.2)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: confidence >= 0.5 ? '#4ade80' : '#fbbf24', width: `${confidence * 100}%` }} />
                  </div>
                  <span style={{ fontSize: '0.9rem', color: '#e0f2fe', minWidth: '50px', textAlign: 'right' }}>
                    {(confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {care && (
          <>
            <CareList title="💊 Treatment Information" items={care.cures} />
            {disease.confidence != null && <CareList title="🛡️ Prevention" items={care.prevention} />}
            {disease.confidence != null && <CareList title="🏥 Self-Care Tips" items={care.self_care} />}
            {disease.confidence != null && care.emergency_signs && care.emergency_signs.length > 0 && (
              <div className="triage-card" style={{ borderLeft: '4px solid #ef4444', background: 'rgba(239, 68, 68, 0.08)' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#fca5a5' }}>🚨 Seek Emergency Care If:</h3>
                <ul style={{ ...listStyle, color: '#fca5a5' }}>
                  {care.emergency_signs.map((sign, i) => <li key={i}>{sign}</li>)}
                </ul>
              </div>
            )}
          </>
        )}

        <OtcProducts products={care?.otc_products} />

        <Disclaimer text={care
          ? 'This assessment is based on AI analysis of your symptoms. It is NOT a medical diagnosis.'
          : triage?.disclaimer || 'Please consult a licensed healthcare professional before making any medical decisions.'
        } />
      </div>
    );
  }

  if (triage) {
    if (!triage.level) return null;
    const levelClass = triage.level.replace(' ', '-');

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className={`triage-card ${levelClass}`}>
          <span className={`severity-badge ${levelClass}`}>{triage.level}</span>
          <h3 style={{ marginBottom: '0.75rem', fontSize: '1.2rem', letterSpacing: '-0.02em' }}>Assessment Summary</h3>
          <p style={{ fontSize: '1rem', lineHeight: '1.6', marginBottom: '1.25rem', color: '#cbd5e1' }}>
            {triage.reasoning}
          </p>

          {triage.red_flags && triage.red_flags.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <strong style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.05em' }}>Red Flags to Monitor</strong>
              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem', fontSize: '0.95rem', color: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {triage.red_flags.map((flag, i) => <li key={i}>{flag}</li>)}
              </ul>
            </div>
          )}

          {triage.remedies && triage.remedies.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <strong style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.05em' }}>Suggested Remedies</strong>
              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.5rem', fontSize: '0.95rem', color: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {triage.remedies.map((remedy, i) => <li key={i}>{remedy}</li>)}
              </ul>
            </div>
          )}

          {triage.guideline_source && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#64748b', textAlign: 'right' }}>
              Grounded via {triage.guideline_source}
            </div>
          )}
        </div>

        <CareList title="💊 AI Care Advice" items={care?.cures} />
        <CareList title="🏥 Self-Care Tips" items={care?.self_care} />
        <OtcProducts products={care?.otc_products} />

        <Disclaimer text={triage.disclaimer || 'This is an AI-assisted assessment only. It is NOT a medical diagnosis. Always consult a licensed healthcare professional before making any medical decisions.'} />
      </div>
    );
  }

  return null;
};

export default TriageResult;
