import React from 'react';

const TriageResult = ({ triage, disease, care, symptoms, severity }) => {
  if (!triage && !disease) return null;

  // New diagnosed format
  if (disease) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Disease Header */}
        <div className="triage-card" style={{ borderLeft: '4px solid #3b82f6' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.75rem', margin: 0, color: '#f1f5f9' }}>
              {disease.name}
            </h2>
            {disease.confidence != null && (
              <div style={{
                background: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid rgba(59, 130, 246, 0.4)',
                borderRadius: '8px',
                padding: '0.5rem 1rem',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase' }}>Confidence</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#60a5fa' }}>
                  {disease.confidence_pct}
                </div>
              </div>
            )}
          </div>

          {/* Confidence Bar — only when confidence is known */}
          {disease.confidence != null && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{
                height: '8px',
                background: 'rgba(148, 163, 184, 0.3)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  background: 'linear-gradient(to right, #60a5fa, #3b82f6)',
                  width: `${Math.min(disease.confidence * 100, 100)}%`,
                  transition: 'width 0.5s ease'
                }}></div>
              </div>
            </div>
          )}

          {/* Current Symptoms */}
          {symptoms && symptoms.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Your Reported Symptoms
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {symptoms.map((symptom, i) => (
                  <span
                    key={i}
                    style={{
                      background: 'rgba(59, 130, 246, 0.15)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: '6px',
                      padding: '0.35rem 0.75rem',
                      fontSize: '0.85rem',
                      color: '#e0f2fe'
                    }}
                  >
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

        {/* Top Predictions */}
        {disease.all_predictions && disease.all_predictions.length > 0 && (
          <div className="triage-card">
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#f1f5f9' }}>
              Top Diagnostic Possibilities
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {disease.all_predictions.map(([name, confidence], idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{ color: '#94a3b8', minWidth: '120px' }}>
                    {name}
                  </span>
                  <div style={{
                    flex: 1,
                    height: '6px',
                    background: 'rgba(148, 163, 184, 0.2)',
                    borderRadius: '3px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      height: '100%',
                      background: confidence >= 0.5 ? '#4ade80' : '#fbbf24',
                      width: `${confidence * 100}%`
                    }}></div>
                  </div>
                  <span style={{ 
                    fontSize: '0.9rem', 
                    color: '#e0f2fe',
                    minWidth: '50px',
                    textAlign: 'right'
                  }}>
                    {(confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Care Information — only show sections with real LLM content */}
        {care && (
          <>
            {care.cures && care.cures.length > 0 && (
              <div className="triage-card">
                <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#f1f5f9' }}>
                  💊 Treatment Information
                </h3>
                <ul style={{
                  paddingLeft: '1.2rem',
                  fontSize: '0.95rem',
                  color: '#cbd5e1',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}>
                  {care.cures.map((cure, i) => (
                    <li key={i}>{cure}</li>
                  ))}
                </ul>
              </div>
            )}

            {disease.confidence != null && care.prevention && care.prevention.length > 0 && (
              <div className="triage-card">
                <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#f1f5f9' }}>
                  🛡️ Prevention
                </h3>
                <ul style={{
                  paddingLeft: '1.2rem',
                  fontSize: '0.95rem',
                  color: '#cbd5e1',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}>
                  {care.prevention.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {disease.confidence != null && care.self_care && care.self_care.length > 0 && (
              <div className="triage-card">
                <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#f1f5f9' }}>
                  🏥 Self-Care Tips
                </h3>
                <ul style={{
                  paddingLeft: '1.2rem',
                  fontSize: '0.95rem',
                  color: '#cbd5e1',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}>
                  {care.self_care.map((tip, i) => (
                    <li key={i}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}

            {disease.confidence != null && care.emergency_signs && care.emergency_signs.length > 0 && (
              <div className="triage-card" style={{
                borderLeft: '4px solid #ef4444',
                background: 'rgba(239, 68, 68, 0.08)'
              }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#fca5a5' }}>
                  🚨 Seek Emergency Care If:
                </h3>
                <ul style={{
                  paddingLeft: '1.2rem',
                  fontSize: '0.95rem',
                  color: '#fca5a5',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}>
                  {care.emergency_signs.map((sign, i) => (
                    <li key={i}>{sign}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {/* Disclaimer */}
        <div style={{ 
          padding: '1rem', 
          background: 'rgba(0,0,0,0.3)', 
          borderRadius: '12px', 
          fontSize: '0.85rem', 
          lineHeight: '1.5',
          color: '#fca5a5',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}>
          ⚠️ {care ? 'This assessment is based on AI analysis of your symptoms. It is NOT a medical diagnosis.' : triage?.disclaimer || 'Please consult a licensed healthcare professional before making any medical decisions.'}
        </div>
      </div>
    );
  }

  // Old triage level format
  if (triage) {
    const levelClass = triage.level.replace(' ', '-');

    return (
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

        <div style={{ 
          padding: '1rem', 
          background: 'rgba(0,0,0,0.3)', 
          borderRadius: '12px', 
          fontSize: '0.85rem', 
          lineHeight: '1.5',
          color: '#fca5a5',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          marginTop: '1rem'
        }}>
          {triage.disclaimer}
        </div>
        
        {triage.guideline_source && (
          <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#64748b', textAlign: 'right' }}>
            Grounded via {triage.guideline_source}
          </div>
        )}
      </div>
    );
  }

  return null;
};

export default TriageResult;
