import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Hash, CheckCircle, Clock, FileText } from 'lucide-react';

export interface AuditEntry {
  id: string;
  hash: string;
  timestamp: string;
  status: 'GOVERNED' | 'ANONYMIZED' | 'VERIFIED';
  type: string;
}

interface AuditLogProps {
  logs: AuditEntry[];
}

const AuditLog: React.FC<AuditLogProps> = ({ logs }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'GOVERNED':
        return 'text-emerald-500 bg-emerald-50/80 border-emerald-200/50';
      case 'ANONYMIZED':
        return 'text-sky-500 bg-sky-50/80 border-sky-200/50';
      case 'VERIFIED':
        return 'text-amber-500 bg-amber-50/80 border-amber-200/50';
      default:
        return 'text-muted-foreground bg-white/40 border-white/50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'GOVERNED':
        return <Shield className="w-3 h-3" />;
      case 'ANONYMIZED':
        return <CheckCircle className="w-3 h-3" />;
      case 'VERIFIED':
        return <Hash className="w-3 h-3" />;
      default:
        return <FileText className="w-3 h-3" />;
    }
  };

  return (
    <div className="w-full flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-1 py-2 border-b border-white/30 mb-3">
        <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
          <Shield className="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold">Audit Trail</h3>
          <p className="text-[11px] text-muted-foreground">SHA-256 governance hashes</p>
        </div>
      </div>

      {/* Log List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin -mx-1 px-1">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Shield className="w-10 h-10 text-muted-foreground/20 mb-3" />
            <p className="text-sm text-muted-foreground/50">No audit entries yet</p>
            <p className="text-xs text-muted-foreground/35 mt-1 max-w-[200px]">
              Interactions will be logged with SHA-256 hashes for compliance
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {logs.map((log, index) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ delay: index * 0.05 }}
                className="mb-2 p-3 rounded-xl bg-white/40 border border-white/50"
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-medium border ${getStatusColor(log.status)}`}
                  >
                    {getStatusIcon(log.status)}
                    {log.status}
                  </span>
                  <span className="text-[10px] text-muted-foreground/50 flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5" />
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <Hash className="w-3 h-3 text-muted-foreground/35 mt-0.5 flex-shrink-0" />
                  <p className="text-[10px] font-mono text-muted-foreground/60 break-all leading-relaxed">
                    {log.hash}
                  </p>
                </div>
                <p className="text-[10px] text-muted-foreground/40 mt-1.5 ml-5">{log.type}</p>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      <div className="px-1 pt-3 border-t border-white/30 mt-3">
        <div className="flex items-center justify-between text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Shield className="w-3 h-3 text-primary" />
            HIPAA Compliant
          </span>
          <span>{logs.length} entries</span>
        </div>
      </div>
    </div>
  );
};

export default AuditLog;
