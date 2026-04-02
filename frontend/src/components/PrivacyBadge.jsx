import React from 'react';
import { motion } from 'framer-motion';

const PrivacyBadge = ({ privacy }) => {
  if (!privacy) return null;

  const isDetected = privacy.pii_detected;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        fontSize: '0.75rem',
        padding: '0.75rem 1rem',
        borderRadius: '12px',
        background: isDetected ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
        color: isDetected ? '#ef4444' : '#10b981',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        marginBottom: '0.75rem',
        border: `1px solid ${isDetected ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`,
        width: 'fit-content'
      }}
    >
      <span style={{ fontSize: '1.1rem' }}>{isDetected ? '🛡️' : '✅'}</span>
      <div>
        <div style={{ fontWeight: '700', marginBottom: '1px' }}>
          {isDetected ? 'PII Redacted' : 'Privacy Verified'}
        </div>
        <div style={{ opacity: 0.8, fontSize: '0.7rem' }}>{privacy.message}</div>
      </div>
    </motion.div>
  );
};

export default PrivacyBadge;
