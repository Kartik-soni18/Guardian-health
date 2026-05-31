import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

interface RejectedMessageProps {
  content?: string;
}

const RejectedMessage: React.FC<RejectedMessageProps> = ({
  content = "I'm designed to assist with health-related questions only. For general queries, please consult a search engine or appropriate service.",
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full p-5 rounded-2xl bg-amber-50/70 border border-amber-200/50"
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl bg-amber-100 flex items-center justify-center flex-shrink-0 border border-amber-200/50">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
        </div>
        <div>
          <h4 className="text-sm font-medium text-amber-600 mb-1">Non-Health Query</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">{content}</p>
        </div>
      </div>
    </motion.div>
  );
};

export default RejectedMessage;
