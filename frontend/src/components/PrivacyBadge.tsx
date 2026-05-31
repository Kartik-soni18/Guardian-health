import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, ShieldAlert } from 'lucide-react';

interface PrivacyBadgeProps {
  piiDetected: boolean;
}

const PrivacyBadge: React.FC<PrivacyBadgeProps> = ({ piiDetected }) => {
  if (piiDetected) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50/80 border border-amber-200/50 text-amber-600 text-[11px] font-medium"
      >
        <ShieldAlert className="w-3 h-3" />
        <span>PII Redacted</span>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50/80 border border-emerald-200/50 text-emerald-600 text-[11px] font-medium"
    >
      <ShieldCheck className="w-3 h-3" />
      <span>Privacy Verified</span>
    </motion.div>
  );
};

export default PrivacyBadge;
