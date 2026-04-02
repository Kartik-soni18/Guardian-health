import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * ResearchOverview
 * ────────────────
 * Displays the PubMed research results beneath a triage card.
 *
 * Props
 *   research : {
 *     summary     : string   — AI-generated research overview
 *     articles    : Array<{pmid, title, abstract, url, year, journal}>
 *     source      : string   — "PubMed / NCBI"
 *     query_used  : string
 *     total_found : number
 *   }
 */
const ResearchOverview = ({ research }) => {
  const [expanded, setExpanded] = useState(false);

  if (!research || (!research.summary && !research.articles?.length)) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      style={{
        marginTop:    '1rem',
        background:   'rgba(16, 185, 129, 0.04)',
        border:       '1px solid rgba(16, 185, 129, 0.2)',
        borderRadius: '16px',
        overflow:     'hidden',
      }}
    >
      {/* ── Header with PubMed badge ── */}
      <div
        style={{
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'space-between',
          padding:        '1rem 1.25rem 0.75rem',
          borderBottom:   '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Verified Source badge */}
          <span
            style={{
              display:       'inline-flex',
              alignItems:    'center',
              gap:           '0.35rem',
              background:    'rgba(16, 185, 129, 0.12)',
              border:        '1px solid rgba(16, 185, 129, 0.35)',
              borderRadius:  '99px',
              padding:       '0.2rem 0.75rem',
              fontSize:      '0.7rem',
              fontWeight:    700,
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
              color:         '#10b981',
            }}
          >
            <span>✓</span> Verified Source: PubMed
          </span>

          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            {research.total_found} article{research.total_found !== 1 ? 's' : ''} retrieved
          </span>
        </div>

        {/* Toggle button */}
        {research.articles?.length > 0 && (
          <button
            onClick={() => setExpanded(v => !v)}
            style={{
              background:   'transparent',
              border:       '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color:        '#94a3b8',
              fontSize:     '0.75rem',
              padding:      '0.3rem 0.7rem',
              cursor:       'pointer',
            }}
          >
            {expanded ? 'Hide abstracts ▲' : 'Show abstracts ▼'}
          </button>
        )}
      </div>

      {/* ── AI-generated research summary ── */}
      <div style={{ padding: '1rem 1.25rem' }}>
        <p
          style={{
            margin:     0,
            fontSize:   '0.9rem',
            lineHeight: 1.7,
            color:      '#cbd5e1',
          }}
        >
          {research.summary}
        </p>
      </div>

      {/* ── Medical Disclaimer ── */}
      <div
        style={{
          margin:       '0 1.25rem 1rem',
          padding:      '0.75rem 1rem',
          background:   'rgba(0,0,0,0.25)',
          borderRadius: '10px',
          border:       '1px solid rgba(239, 68, 68, 0.15)',
        }}
      >
        <p
          style={{
            margin:     0,
            fontSize:   '0.78rem',
            lineHeight: 1.5,
            color:      '#fca5a5',
            fontWeight: 600,
          }}
        >
          ⚠️ <strong>Medical Disclaimer:</strong> This research overview is sourced from
          PubMed/NCBI for informational purposes only. It does NOT constitute medical
          advice, diagnosis, or treatment. Always consult a licensed healthcare professional
          before making any health decisions.
        </p>
      </div>

      {/* ── Expandable article list ── */}
      <AnimatePresence>
        {expanded && research.articles?.length > 0 && (
          <motion.div
            key="articles"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: 'hidden' }}
          >
            <div
              style={{
                borderTop: '1px solid rgba(255,255,255,0.06)',
                padding:   '1rem 1.25rem',
                display:   'flex',
                flexDirection: 'column',
                gap:       '1rem',
              }}
            >
              {research.articles.map((article, i) => (
                <ArticleCard key={article.pmid} article={article} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Footer ── */}
      {research.query_used && (
        <div
          style={{
            padding:    '0.5rem 1.25rem 0.75rem',
            fontSize:   '0.7rem',
            color:      '#475569',
            textAlign:  'right',
          }}
        >
          PubMed query: <em>"{research.query_used}"</em>
        </div>
      )}
    </motion.div>
  );
};


const ArticleCard = ({ article, index }) => {
  const [showAbstract, setShowAbstract] = useState(false);

  return (
    <div
      style={{
        background:   'rgba(255,255,255,0.03)',
        border:       '1px solid rgba(255,255,255,0.08)',
        borderRadius: '10px',
        padding:      '0.875rem 1rem',
      }}
    >
      {/* Article number + journal */}
      <div
        style={{
          display:    'flex',
          alignItems: 'center',
          gap:        '0.5rem',
          marginBottom: '0.4rem',
        }}
      >
        <span
          style={{
            background:    'rgba(59,130,246,0.15)',
            color:         '#60a5fa',
            borderRadius:  '99px',
            fontSize:      '0.65rem',
            fontWeight:    700,
            padding:       '0.1rem 0.5rem',
          }}
        >
          [{index + 1}]
        </span>
        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
          {article.journal} · {article.year}
        </span>
      </div>

      {/* Title (external link to PubMed) */}
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          fontSize:       '0.875rem',
          fontWeight:     600,
          color:          '#93c5fd',
          textDecoration: 'none',
          lineHeight:     1.4,
          display:        'block',
          marginBottom:   '0.5rem',
        }}
      >
        {article.title}
      </a>

      {/* Toggle abstract */}
      <button
        onClick={() => setShowAbstract(v => !v)}
        style={{
          background:   'transparent',
          border:       'none',
          color:        '#475569',
          fontSize:     '0.72rem',
          cursor:       'pointer',
          padding:      0,
        }}
      >
        {showAbstract ? '▲ Hide abstract' : '▼ Read abstract'}
      </button>

      <AnimatePresence>
        {showAbstract && (
          <motion.p
            key="abstract"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{
              margin:     '0.6rem 0 0',
              fontSize:   '0.8rem',
              lineHeight: 1.6,
              color:      '#94a3b8',
              overflow:   'hidden',
            }}
          >
            {article.abstract}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ResearchOverview;
