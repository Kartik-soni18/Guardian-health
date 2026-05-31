import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import type { Message } from '@/hooks/useTriage';
import TriageResult from './TriageResult';
import RejectedMessage from './RejectedMessage';
import type { AuditEntry } from '@/App';
import {
  Send,
  User,
  Sparkles,
  ArrowRight,
  Shield,
  Activity,
  Clock,
  Lock,
  HeartPulse,
  Stethoscope,
  Thermometer,
  Wind,
} from 'lucide-react';

interface ChatInterfaceProps {
  messages: Message[];
  loading: boolean;
  sendMessage: (query: string, history: Message[]) => Promise<Message | undefined>;
  onNewLog?: (entry: AuditEntry) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  loading,
  sendMessage,
  onNewLog,
}) => {
  const { user } = useAuth();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const query = input.trim();
    setInput('');
    const history: Message[] = [...messages];
    const botMessage = await sendMessage(query, history);

    if (botMessage?.metadata?.audit && onNewLog) {
      const audit = botMessage.metadata.audit as { interaction_id: string; audit_hash: string };
      onNewLog({
        id: audit.interaction_id,
        hash: audit.audit_hash,
        timestamp: new Date().toISOString(),
        status: 'GOVERNED',
        type: (botMessage.type as string) || 'triage',
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleForceTriage = () => {
    setInput("That's it. Just give me results.");
    inputRef.current?.focus();
  };

  const suggestedQueries = [
    "I have a headache, fever, and body aches",
    "My child has a rash and is itching",
    "I feel chest tightness and shortness of breath",
  ];

  const quickActions = [
    { label: 'Fever', icon: <Thermometer className="w-3.5 h-3.5" />, color: 'bg-rose-50 text-rose-500 border-rose-200 hover:bg-rose-100 hover:border-rose-300' },
    { label: 'Cough', icon: <Wind className="w-3.5 h-3.5" />, color: 'bg-sky-50 text-sky-500 border-sky-200 hover:bg-sky-100 hover:border-sky-300' },
    { label: 'Headache', icon: <Activity className="w-3.5 h-3.5" />, color: 'bg-violet-50 text-violet-500 border-violet-200 hover:bg-violet-100 hover:border-violet-300' },
    { label: 'Stomach Pain', icon: <HeartPulse className="w-3.5 h-3.5" />, color: 'bg-emerald-50 text-emerald-500 border-emerald-200 hover:bg-emerald-100 hover:border-emerald-300' },
  ];

  return (
    <div className="flex flex-col h-full glass-card rounded-2xl overflow-hidden">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-5 py-6">
        {messages.length === 0 ? (
          /* Welcome Screen */
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto text-center"
          >
            {/* Logo */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/20 via-primary/10 to-transparent flex items-center justify-center mb-6 shadow-glow pulse-soft"
            >
              <Sparkles className="w-9 h-9 text-primary" />
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-3xl font-bold mb-3 text-gradient"
            >
              GuardianHealth Triage
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-sm text-muted-foreground max-w-md mb-10 leading-relaxed"
            >
              Describe your symptoms and our AI will analyze them to provide triage guidance,
              possible conditions, and care recommendations.
            </motion.p>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex flex-wrap justify-center gap-2.5 mb-10"
            >
              {quickActions.map((action, idx) => (
                <motion.button
                  key={action.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + idx * 0.08 }}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setInput(`I have ${action.label.toLowerCase()}`);
                    inputRef.current?.focus();
                  }}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${action.color}`}
                >
                  {action.icon}
                  {action.label}
                </motion.button>
              ))}
            </motion.div>

            {/* Suggested Queries */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="w-full space-y-2.5"
            >
              <p className="text-xs text-muted-foreground/60 mb-3">Or try one of these:</p>
              {suggestedQueries.map((query, idx) => (
                <motion.button
                  key={idx}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + idx * 0.1 }}
                  whileHover={{ scale: 1.01, x: 4 }}
                  onClick={() => {
                    setInput(query);
                    inputRef.current?.focus();
                  }}
                  className="w-full flex items-center justify-between p-4 rounded-2xl glass border border-white/60 hover:bg-white/60 transition-all text-left group"
                >
                  <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                    {query}
                  </span>
                  <ArrowRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                </motion.button>
              ))}
            </motion.div>

            {/* Trust Badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="flex items-center gap-5 mt-10"
            >
              {[
                { icon: <Shield className="w-3.5 h-3.5" />, label: 'HIPAA Compliant' },
                { icon: <Lock className="w-3.5 h-3.5" />, label: 'End-to-End Encrypted' },
                { icon: <Clock className="w-3.5 h-3.5" />, label: '24/7 Available' },
              ].map((badge) => (
                <div key={badge.label} className="flex items-center gap-1.5 text-[11px] text-muted-foreground/50">
                  {badge.icon}
                  <span>{badge.label}</span>
                </div>
              ))}
            </motion.div>
          </motion.div>
        ) : (
          /* Message List */
          <div className="max-w-3xl mx-auto space-y-5">
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <motion.div
                  key={msg.id || idx}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35, ease: 'easeOut' }}
                >
                  {msg.role === 'user' ? (
                    /* User Message */
                    <div className="flex items-start justify-end gap-3">
                      <div className="max-w-[80%] p-4 rounded-2xl rounded-tr-md bg-gradient-to-br from-primary to-primary/90 text-primary-foreground shadow-glow">
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                        <p className="text-[10px] text-primary-foreground/60 mt-2 text-right">
                          {msg.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                      <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0 border border-primary/20">
                        <User className="w-4 h-4 text-primary" />
                      </div>
                    </div>
                  ) : (
                    /* Bot Message */
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-secondary to-secondary/50 flex items-center justify-center flex-shrink-0 border border-white/60">
                        <Stethoscope className="w-4 h-4 text-primary" />
                      </div>
                      <div className="flex-1 max-w-[85%] space-y-3">
                        {msg.type === 'rejected' ? (
                          <RejectedMessage content={msg.content} />
                        ) : msg.type === 'follow_up' ? (
                          <div className="space-y-3">
                            <div className="p-5 rounded-2xl glass-card border border-white/60">
                              <p className="text-sm text-foreground leading-relaxed">
                                {msg.content}
                              </p>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={handleForceTriage}
                              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-all border border-primary/20"
                            >
                              <Sparkles className="w-4 h-4" />
                              Give me results with current information
                            </motion.button>
                          </div>
                        ) : msg.metadata ? (
                          <TriageResult
                            data={msg.metadata as Record<string, unknown>}
                            type={msg.type as string}
                            privacy={msg.privacy}
                          />
                        ) : (
                          <div className="p-5 rounded-2xl glass-card border border-white/60">
                            <p className="text-sm text-foreground leading-relaxed">
                              {msg.content}
                            </p>
                          </div>
                        )}
                        <p className="text-[10px] text-muted-foreground/40 ml-1">
                          {msg.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Loading Indicator */}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3"
              >
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-secondary to-secondary/50 flex items-center justify-center flex-shrink-0 border border-white/60">
                  <Stethoscope className="w-4 h-4 text-primary" />
                </div>
                <div className="flex items-center gap-2 p-4 rounded-2xl glass-card border border-white/60">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-primary typing-dot" />
                    <div className="w-2 h-2 rounded-full bg-primary typing-dot" />
                    <div className="w-2 h-2 rounded-full bg-primary typing-dot" />
                  </div>
                  <span className="text-xs text-muted-foreground ml-1">Analyzing symptoms...</span>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="glass-strong border-t border-white/60 px-5 py-4">
        <div className="max-w-3xl mx-auto">
          {!user && messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-center gap-2 mb-3 p-3 rounded-xl bg-amber-50/80 border border-amber-200/60"
            >
              <Lock className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-xs text-amber-600 font-medium">
                Sign in to start a consultation and save your chat history
              </span>
            </motion.div>
          )}
          <div className="flex items-end gap-2.5">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  user
                    ? "Describe your symptoms..."
                    : "Sign in to start a consultation..."
                }
                disabled={loading || !user}
                rows={1}
                className="w-full px-5 py-3.5 pr-14 rounded-2xl glass-input text-foreground placeholder:text-muted-foreground/40 focus:outline-none transition-all resize-none disabled:opacity-50 disabled:cursor-not-allowed scrollbar-thin text-sm"
                style={{ minHeight: '52px', maxHeight: '120px' }}
              />
              {input.length > 0 && (
                <button
                  onClick={() => setInput('')}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/60 transition-colors"
                >
                  <span className="text-[10px] font-medium">Clear</span>
                </button>
              )}
            </div>
            <motion.button
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.94 }}
              onClick={handleSend}
              disabled={loading || !input.trim() || !user}
              className="p-3.5 rounded-2xl bg-primary text-primary-foreground shadow-glow hover:shadow-lg disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none transition-all flex-shrink-0"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </motion.button>
          </div>
          <p className="text-[10px] text-muted-foreground/40 text-center mt-2.5">
            AI-generated triage for informational purposes only. Not a substitute for professional medical advice.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
