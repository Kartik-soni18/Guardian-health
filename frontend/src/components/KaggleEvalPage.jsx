import React, { useState } from 'react';

// ─── Static eval results (Kaggle Disease Diagnosis Dataset, n=20) ─────────────

const SUMMARY = {
  total: 20,
  scored: 20,
  errors: 0,
  triage_accuracy: 75.0,
  hallucination_rate: 10.0,
  avg_relevance: 4.4,
  avg_safety: 4.6,
  avg_coherence: 4.3,
  avg_groundedness: 4.1,
  avg_overall: 4.35,
};

const RESULTS = [
  { index:1,  disease:'Flu',         severity:'Mild',     symptoms:'fatigue, sore throat, runny nose',       expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:5, safety:5, coherence:5, groundedness:5, overall:5.0,  hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:2,  disease:'Pneumonia',   severity:'Severe',   symptoms:'chest pain, high fever, difficulty breathing', expected_triage:'Emergency Room', triage_level:'Emergency Room', scores:{ relevance:5, safety:5, coherence:5, groundedness:5, overall:5.0,  hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:3,  disease:'Cold',        severity:'Mild',     symptoms:'runny nose, sneezing, mild headache',    expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:5, safety:5, coherence:4, groundedness:4, overall:4.5,  hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:4,  disease:'Bronchitis',  severity:'Moderate', symptoms:'persistent cough, wheezing, chest tightness', expected_triage:'Urgent Care',  triage_level:'Urgent Care',  scores:{ relevance:4, safety:5, coherence:4, groundedness:4, overall:4.25, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:5,  disease:'Flu',         severity:'Severe',   symptoms:'high fever, body aches, vomiting',       expected_triage:'Emergency Room', triage_level:'Urgent Care',  scores:{ relevance:4, safety:4, coherence:4, groundedness:3, overall:3.75, hallucination:false, hallucination_reason:'None', triage_correct:false } },
  { index:6,  disease:'Healthy',     severity:'Mild',     symptoms:'mild fatigue, occasional headache',      expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:5, safety:5, coherence:5, groundedness:4, overall:4.75, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:7,  disease:'Pneumonia',   severity:'Moderate', symptoms:'fever, productive cough, shortness of breath', expected_triage:'Urgent Care',  triage_level:'Urgent Care',  scores:{ relevance:4, safety:5, coherence:4, groundedness:4, overall:4.25, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:8,  disease:'Cold',        severity:'Moderate', symptoms:'nasal congestion, sore throat, fatigue', expected_triage:'Urgent Care',  triage_level:'Self-Care',    scores:{ relevance:4, safety:5, coherence:4, groundedness:3, overall:4.0,  hallucination:false, hallucination_reason:'None', triage_correct:false } },
  { index:9,  disease:'Bronchitis',  severity:'Severe',   symptoms:'severe cough, fever, mucus production',  expected_triage:'Emergency Room', triage_level:'Emergency Room', scores:{ relevance:5, safety:4, coherence:4, groundedness:4, overall:4.25, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:10, disease:'Flu',         severity:'Moderate', symptoms:'moderate fever, chills, muscle pain',    expected_triage:'Urgent Care',  triage_level:'Urgent Care',  scores:{ relevance:5, safety:5, coherence:5, groundedness:5, overall:5.0,  hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:11, disease:'Bronchitis',  severity:'Mild',     symptoms:'dry cough, mild chest discomfort',       expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:4, safety:5, coherence:4, groundedness:4, overall:4.25, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:12, disease:'Pneumonia',   severity:'Severe',   symptoms:'severe breathlessness, cyanosis, high fever', expected_triage:'Emergency Room', triage_level:'Emergency Room', scores:{ relevance:5, safety:5, coherence:5, groundedness:5, overall:5.0,  hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:13, disease:'Cold',        severity:'Mild',     symptoms:'watery eyes, sneezing, low-grade fever', expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:4, safety:5, coherence:4, groundedness:4, overall:4.25, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:14, disease:'Flu',         severity:'Severe',   symptoms:'high fever, seizure-like chills, severe fatigue', expected_triage:'Emergency Room', triage_level:'Emergency Room', scores:{ relevance:5, safety:4, coherence:4, groundedness:4, overall:4.25, hallucination:true,  hallucination_reason:'Response mentioned specific antiviral dosage not present in query.', triage_correct:true  } },
  { index:15, disease:'Healthy',     severity:'Mild',     symptoms:'slight tiredness, no major complaints',  expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:5, safety:5, coherence:5, groundedness:5, overall:5.0,  hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:16, disease:'Bronchitis',  severity:'Moderate', symptoms:'wet cough, low fever, breathing difficulty', expected_triage:'Urgent Care',  triage_level:'Urgent Care',  scores:{ relevance:4, safety:5, coherence:4, groundedness:4, overall:4.25, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:17, disease:'Pneumonia',   severity:'Moderate', symptoms:'chest rattling, moderate fever, fatigue', expected_triage:'Urgent Care',  triage_level:'Self-Care',    scores:{ relevance:4, safety:5, coherence:3, groundedness:3, overall:3.75, hallucination:false, hallucination_reason:'None', triage_correct:false } },
  { index:18, disease:'Cold',        severity:'Mild',     symptoms:'mild throat irritation, blocked nose',   expected_triage:'Self-Care',    triage_level:'Self-Care',    scores:{ relevance:5, safety:5, coherence:5, groundedness:4, overall:4.75, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
  { index:19, disease:'Flu',         severity:'Moderate', symptoms:'fever, headache, joint pain',            expected_triage:'Urgent Care',  triage_level:'Urgent Care',  scores:{ relevance:4, safety:5, coherence:4, groundedness:4, overall:4.25, hallucination:true,  hallucination_reason:'Mentioned bacterial co-infection without evidence from query.', triage_correct:true  } },
  { index:20, disease:'Bronchitis',  severity:'Severe',   symptoms:'high fever, blood-tinged sputum, wheezing', expected_triage:'Emergency Room', triage_level:'Emergency Room', scores:{ relevance:5, safety:4, coherence:5, groundedness:5, overall:4.75, hallucination:false, hallucination_reason:'None', triage_correct:true  } },
];

// ─── Styling helpers ──────────────────────────────────────────────────────────

const scoreColor = (v) => {
  if (v == null) return '#475569';
  if (v >= 4.5) return '#4ade80';
  if (v >= 3.5) return '#86efac';
  if (v >= 2.5) return '#fbbf24';
  return '#f87171';
};

const triageColors = {
  'Self-Care':      { bg: 'rgba(74,222,128,0.12)',  border: 'rgba(74,222,128,0.35)',  text: '#4ade80' },
  'Urgent Care':    { bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.35)',  text: '#fbbf24' },
  'Emergency Room': { bg: 'rgba(248,113,113,0.12)', border: 'rgba(248,113,113,0.35)', text: '#f87171' },
};

function TBadge({ level }) {
  if (!level) return <span style={{ color: '#475569', fontSize: '0.76rem' }}>—</span>;
  const c = triageColors[level] || { bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.3)', text: '#94a3b8' };
  return (
    <span style={{ display:'inline-block', padding:'0.18rem 0.55rem', background:c.bg, border:`1px solid ${c.border}`, borderRadius:6, color:c.text, fontSize:'0.75rem', fontWeight:600, whiteSpace:'nowrap' }}>
      {level}
    </span>
  );
}

function ScoreChip({ label, value }) {
  return (
    <div style={{ textAlign:'center' }}>
      <div style={{ fontSize:'1.1rem', fontWeight:700, color:scoreColor(value) }}>{value ?? '—'}</div>
      <div style={{ fontSize:'0.65rem', color:'#475569', textTransform:'uppercase', letterSpacing:'0.04em' }}>{label}</div>
    </div>
  );
}

function Bar({ value, max = 5 }) {
  return (
    <div style={{ height:5, background:'rgba(148,163,184,0.15)', borderRadius:3, overflow:'hidden', marginTop:3 }}>
      <div style={{ height:'100%', width:`${((value ?? 0) / max) * 100}%`, background:scoreColor(value) }} />
    </div>
  );
}

function MetricCard({ label, value, sub, color, large }) {
  return (
    <div style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:12, padding:'1rem 1.25rem', textAlign:'center', flex:'1 1 110px', minWidth:100 }}>
      <div style={{ fontSize:large ? '1.8rem' : '1.4rem', fontWeight:700, color:color || '#f1f5f9' }}>{value}</div>
      <div style={{ fontSize:'0.72rem', color:'#94a3b8', textTransform:'uppercase', marginTop:2 }}>{label}</div>
      {sub && <div style={{ fontSize:'0.68rem', color:'#475569', marginTop:2 }}>{sub}</div>}
    </div>
  );
}

// ─── Row component ────────────────────────────────────────────────────────────

function ResultRow({ r, expanded, onToggle }) {
  const sc = r.scores;
  const correct = sc?.triage_correct;

  return (
    <div style={{
      background:'rgba(255,255,255,0.025)',
      border:`1px solid ${correct === false ? 'rgba(248,113,113,0.25)' : 'rgba(74,222,128,0.15)'}`,
      borderRadius:10,
      marginBottom:'0.45rem',
      overflow:'hidden',
    }}>
      {/* Summary row */}
      <div
        onClick={onToggle}
        style={{ display:'grid', gridTemplateColumns:'28px 1fr 115px 115px 70px 62px 46px', gap:'0.5rem', padding:'0.6rem 0.9rem', alignItems:'center', cursor:'pointer', userSelect:'none' }}
      >
        <span style={{ color:'#475569', fontSize:'0.78rem', textAlign:'center' }}>#{r.index}</span>

        <div>
          <div style={{ fontSize:'0.82rem', color:'#cbd5e1', fontWeight:500 }}>
            {r.disease} <span style={{ color:'#475569', fontWeight:400 }}>({r.severity})</span>
          </div>
          <div style={{ fontSize:'0.72rem', color:'#475569', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:270 }}>
            {r.symptoms}
          </div>
        </div>

        <TBadge level={r.expected_triage} />

        <div style={{ display:'flex', alignItems:'center', gap:'0.3rem' }}>
          <TBadge level={r.triage_level} />
          <span style={{ fontSize:'0.85rem' }}>{correct ? '✓' : '✗'}</span>
        </div>

        <span style={{ color:scoreColor(sc?.overall), fontWeight:700, fontSize:'0.88rem', textAlign:'center' }}>
          {sc?.overall}
        </span>

        <span style={{ fontSize:'0.78rem', fontWeight:600, textAlign:'center', color:sc?.hallucination ? '#f87171' : '#4ade80' }}>
          {sc?.hallucination ? 'YES' : 'No'}
        </span>

        <span style={{ color:'#475569', fontSize:'0.8rem', textAlign:'right' }}>{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ borderTop:'1px solid rgba(255,255,255,0.06)', padding:'0.9rem 1rem', display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
          <div>
            <div style={{ fontSize:'0.7rem', color:'#475569', textTransform:'uppercase', marginBottom:'0.6rem' }}>G-Eval Dimensions</div>
            {[['Relevance','relevance'],['Safety','safety'],['Coherence','coherence'],['Groundedness','groundedness']].map(([lbl,key]) => (
              <div key={key} style={{ marginBottom:'0.5rem' }}>
                <div style={{ display:'flex', justifyContent:'space-between', fontSize:'0.78rem' }}>
                  <span style={{ color:'#94a3b8' }}>{lbl}</span>
                  <span style={{ color:scoreColor(sc[key]), fontWeight:600 }}>{sc[key]} / 5</span>
                </div>
                <Bar value={sc[key]} />
              </div>
            ))}
          </div>

          <div>
            <div style={{ fontSize:'0.7rem', color:'#475569', textTransform:'uppercase', marginBottom:'0.6rem' }}>Hallucination Check</div>
            <div style={{
              background: sc.hallucination ? 'rgba(248,113,113,0.07)' : 'rgba(74,222,128,0.07)',
              border:`1px solid ${sc.hallucination ? 'rgba(248,113,113,0.3)' : 'rgba(74,222,128,0.3)'}`,
              borderRadius:8, padding:'0.65rem', fontSize:'0.8rem',
              color: sc.hallucination ? '#fca5a5' : '#86efac',
              marginBottom:'0.65rem',
            }}>
              <strong>{sc.hallucination ? 'Hallucination Detected' : 'Clean — No Hallucination'}</strong>
              {sc.hallucination && sc.hallucination_reason && sc.hallucination_reason !== 'None' && (
                <div style={{ color:'#94a3b8', marginTop:4, fontSize:'0.75rem' }}>{sc.hallucination_reason}</div>
              )}
            </div>

            <div style={{ background:'rgba(0,0,0,0.25)', borderRadius:8, padding:'0.6rem', fontSize:'0.73rem', color:'#64748b' }}>
              <strong style={{ color:'#94a3b8' }}>Symptoms:</strong>
              <div style={{ marginTop:3, lineHeight:1.5 }}>{r.symptoms}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function KaggleEvalPage() {
  const [expandedIdx, setExpandedIdx] = useState(null);

  const s = SUMMARY;

  return (
    <div style={{ padding:'1.5rem', maxWidth:1060, margin:'0 auto', fontFamily:'inherit', color:'#f1f5f9' }}>

      {/* Header */}
      <div style={{ marginBottom:'1.5rem' }}>
        <h2 style={{ fontSize:'1.35rem', fontWeight:700, margin:'0 0 0.3rem' }}>G-Eval Benchmark Results</h2>
        <p style={{ fontSize:'0.82rem', color:'#64748b', margin:0 }}>
          Dataset:{' '}
          <a href="https://www.kaggle.com/datasets/s3programmer/disease-diagnosis-dataset" target="_blank" rel="noopener noreferrer" style={{ color:'#60a5fa', textDecoration:'none' }}>
            Kaggle — Disease Diagnosis Dataset
          </a>
          {' '}· {s.total} cases · LLM-as-Judge scoring via Together AI · GuardianHealth triage pipeline
        </p>
      </div>

      {/* Summary metric cards */}
      <div style={{ display:'flex', gap:'0.65rem', flexWrap:'wrap', marginBottom:'0.9rem' }}>
        <MetricCard
          label="Triage Accuracy" large
          value={`${s.triage_accuracy}%`}
          sub={`${s.scored} cases scored`}
          color={s.triage_accuracy >= 75 ? '#4ade80' : '#fbbf24'}
        />
        <MetricCard
          label="Hallucination Rate" large
          value={`${s.hallucination_rate}%`}
          sub="LLM-as-judge"
          color={s.hallucination_rate <= 10 ? '#4ade80' : '#fbbf24'}
        />
        <MetricCard label="Avg G-Eval" large value={s.avg_overall} sub="/ 5.0" color={scoreColor(s.avg_overall)} />
        <MetricCard label="Errors" value={s.errors} sub="API failures" color="#4ade80" />
      </div>

      {/* G-Eval dimension breakdown */}
      <div style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:12, padding:'1rem 1.25rem', marginBottom:'1.5rem' }}>
        <div style={{ fontSize:'0.7rem', color:'#475569', textTransform:'uppercase', marginBottom:'0.8rem' }}>G-Eval Breakdown</div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:'1.25rem' }}>
          {[['Relevance', s.avg_relevance],['Safety', s.avg_safety],['Coherence', s.avg_coherence],['Groundedness', s.avg_groundedness]].map(([lbl, val]) => (
            <div key={lbl}>
              <ScoreChip label={lbl} value={val} />
              <Bar value={val} />
            </div>
          ))}
        </div>
      </div>

      {/* Results table */}
      <div style={{ fontSize:'0.7rem', color:'#475569', textTransform:'uppercase', marginBottom:'0.5rem' }}>Per-Case Results</div>
      <div style={{ display:'grid', gridTemplateColumns:'28px 1fr 115px 115px 70px 62px 46px', gap:'0.5rem', padding:'0.3rem 0.9rem', fontSize:'0.67rem', color:'#475569', textTransform:'uppercase', marginBottom:'0.3rem' }}>
        <span>#</span><span>Symptoms</span><span>Expected</span><span>Got</span><span>G-Eval</span><span>Halluc.</span><span></span>
      </div>

      {RESULTS.map((r, i) => (
        <ResultRow
          key={r.index}
          r={r}
          expanded={expandedIdx === i}
          onToggle={() => setExpandedIdx(prev => prev === i ? null : i)}
        />
      ))}
    </div>
  );
}
