import React from 'react';
import { motion } from 'framer-motion';

/**
 * RejectedMessage
 * ───────────────
 * Displayed when the Medical Firewall rejects a non-health query.
 * Renders a friendly, non-alarming explanation inside the chat bubble flow.
 */
const RejectedMessage = () => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    style={{
      background:   'rgba(245, 158, 11, 0.07)',
      border:       '1px solid rgba(245, 158, 11, 0.25)',
      borderLeft:   '4px solid #f59e0b',
      borderRadius: '0 16px 16px 16px',
      padding:      '1.25rem 1.5rem',
      maxWidth:     '600px',
    }}
  >
    {/* Header row */}
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
      <span style={{ fontSize: '1.1rem' }}>🛡️</span>
      <span
        style={{
          fontSize:      '0.7rem',
          fontWeight:    700,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color:         '#f59e0b',
        }}
      >
        Outside Scope
      </span>
    </div>

    {/* Message */}
    <p
      style={{
        margin:     0,
        fontSize:   '0.95rem',
        lineHeight: 1.6,
        color:      'rgba(248, 250, 252, 0.85)',
      }}
    >
      I am a specialized medical assistant; I cannot answer non-health related questions.
    </p>

    {/* Hint */}
    <p
      style={{
        margin:    '0.75rem 0 0',
        fontSize:  '0.8rem',
        color:     '#64748b',
        fontStyle: 'italic',
      }}
    >
      Please describe a symptom, health concern, or medical question and I will assist you.
    </p>
  </motion.div>
);

export default RejectedMessage;
