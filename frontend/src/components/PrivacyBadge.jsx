import React from 'react';
import { motion } from 'framer-motion';

const PrivacyBadge = ({ privacy }) => {
  if (!privacy) return null;

  const isDetected = privacy.pii_detected;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        fontSize: '0.72rem',
        padding: '0.4rem 0.75rem',
        borderRadius: '20px',
        background: isDetected ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)',
        color: isDetected ? '#ef4444' : '#10b981',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        marginBottom: '0.6rem',
        border: `1px solid ${isDetected ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.18)'}`,
      }}
    >
      <span style={{ fontSize: '0.85rem' }}>{isDetected ? '🛡️' : '✅'}</span>
      <div>
        <span style={{ fontWeight: '700' }}>
          {isDetected ? 'PII Redacted' : 'Privacy Verified'}
        </span>
        {privacy.message && (
          <span style={{ opacity: 0.75, marginLeft: '0.35rem' }}>— {privacy.message}</span>
        )}
      </div>
    </motion.div>
  );
};

export default PrivacyBadge;
