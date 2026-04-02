import React from 'react';

const AuditLog = ({ logs }) => {
  return (
    <aside className="audit-sidebar" style={{ 
      background: 'var(--panel-dark)', 
      border: '1px solid var(--glass-border)',
      borderRadius: '24px',
      padding: '2rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.5rem',
      height: 'fit-content',
      maxHeight: '700px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6', boxShadow: '0 0 10px #3b82f6' }}></div>
        <h2 style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.15em', fontWeight: '700' }}>
          Governance Audit
        </h2>
      </div>
      
      <div style={{ flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', paddingRight: '0.5rem' }}>
        {logs.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '1rem', opacity: 0.2 }}>📋</div>
            <p style={{ fontSize: '0.85rem', color: '#475569', lineHeight: '1.5' }}>
              No audit records generated. Start a triage session to see real-time interaction hashing.
            </p>
          </div>
        )}
        {logs.map((log, i) => (
          <div key={i} style={{ 
            padding: '1.25rem', 
            background: 'var(--glass-bg)', 
            borderRadius: '16px',
            fontSize: '0.8rem',
            border: '1px solid var(--glass-border)',
            transition: 'all 0.3s ease'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', alignItems: 'center' }}>
              <span style={{ color: '#3b82f6', fontWeight: '700', fontFamily: 'JetBrains Mono' }}>
                ID: {log.interaction_id.slice(0,8)}
              </span>
              <span style={{ color: '#64748b', fontSize: '0.7rem' }}>
                {new Date(log.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
            <div style={{ 
              fontFamily: 'JetBrains Mono, monospace', 
              wordBreak: 'break-all', 
              color: '#94a3b8',
              background: 'rgba(0,0,0,0.4)',
              padding: '0.75rem',
              borderRadius: '8px',
              fontSize: '0.65rem',
              lineHeight: '1.6',
              border: '1px solid rgba(255,255,255,0.05)'
            }}>
              <span style={{ color: '#475569', display: 'block', marginBottom: '0.25rem', fontSize: '0.6rem' }}>SHA-256 AUDIT HASH</span>
              {log.audit_hash}
            </div>
            <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
              <span style={{ padding: '2px 6px', background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '4px', fontSize: '0.6rem', fontWeight: '700' }}>GOVERNED</span>
              <span style={{ padding: '2px 6px', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '4px', fontSize: '0.6rem', fontWeight: '700' }}>ANONYMIZED</span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default AuditLog;
