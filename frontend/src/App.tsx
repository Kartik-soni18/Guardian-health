import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider } from '@/context/AuthContext';
import { useAuth } from '@/context/AuthContext';
import { useTriage } from '@/hooks/useTriage';
import ChatInterface from '@/components/ChatInterface';
import Sidebar from '@/components/Sidebar';
import AuditLog from '@/components/AuditLog';
import AuthModal from '@/components/AuthModal';

import {
  Shield,
  Activity,
  User,
  LogOut,
  Menu,
  X,
  Sparkles,
} from 'lucide-react';

export interface AuditEntry {
  id: string;
  hash: string;
  timestamp: string;
  status: 'GOVERNED' | 'ANONYMIZED' | 'VERIFIED';
  type: string;
}

/* Animated background orbs */
const BackgroundOrbs: React.FC = () => (
  <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
    {/* Orb 1 - Lavender */}
    <div
      className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full float opacity-40"
      style={{
        background: 'radial-gradient(circle, rgba(180,170,245,0.5) 0%, rgba(180,170,245,0) 70%)',
      }}
    />
    {/* Orb 2 - Mint */}
    <div
      className="absolute top-1/3 -right-40 w-[600px] h-[600px] rounded-full float-slow opacity-30"
      style={{
        background: 'radial-gradient(circle, rgba(160,225,200,0.5) 0%, rgba(160,225,200,0) 70%)',
        animationDelay: '2s',
      }}
    />
    {/* Orb 3 - Peach */}
    <div
      className="absolute -bottom-40 left-1/4 w-[450px] h-[450px] rounded-full float opacity-35"
      style={{
        background: 'radial-gradient(circle, rgba(245,200,170,0.5) 0%, rgba(245,200,170,0) 70%)',
        animationDelay: '4s',
      }}
    />
    {/* Orb 4 - Sky */}
    <div
      className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full float-slow opacity-20"
      style={{
        background: 'radial-gradient(circle, rgba(170,210,245,0.4) 0%, rgba(170,210,245,0) 70%)',
        animationDelay: '1s',
      }}
    />
    {/* Subtle noise texture overlay */}
    <div
      className="absolute inset-0 opacity-[0.015]"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
      }}
    />
  </div>
);

const AppContent: React.FC = () => {
  const [activeTab] = useState<'chat'>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const { user, logout } = useAuth();
  const {
    messages,
    loading,
    currentChatId,
    sendMessage,
    loadChat,
    newChat,
  } = useTriage();

  const handleNewChat = useCallback(() => {
    newChat();
    setSidebarOpen(false);
  }, [newChat]);

  const handleSelectChat = useCallback((chatId: string) => {
    loadChat(chatId);
    setSidebarOpen(false);
  }, [loadChat]);

  const handleNewLog = useCallback((entry: AuditEntry) => {
    setLogs(prev => [entry, ...prev]);
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col bg-background overflow-hidden relative">
      <BackgroundOrbs />

      {/* Top Navigation Bar */}
      <header className="h-16 flex-shrink-0 z-20 relative">
        <div className="glass-strong h-full mx-3 mt-3 rounded-2xl border border-white/60 shadow-glass">
          <div className="h-full flex items-center justify-between px-5">
            {/* Left: Logo + Sidebar Toggle */}
            <div className="flex items-center gap-3">
              {user && (
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2.5 rounded-xl hover:bg-white/60 transition-colors lg:hidden"
                >
                  {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
                </button>
              )}
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shadow-glow">
                  <Shield className="w-4.5 h-4.5 text-primary" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-sm font-bold tracking-tight text-gradient">GuardianHealth</h1>
                  <p className="text-[10px] text-muted-foreground -mt-0.5">AI Medical Triage</p>
                </div>
              </div>
            </div>

            {/* Center */}
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary/70" />
              <span className="text-sm font-medium text-muted-foreground">Medical Triage Chat</span>
            </div>

            {/* Right: Auth Actions */}
            <div className="flex items-center gap-2">
              {user ? (
                <div className="flex items-center gap-2">
                  <div className="hidden md:flex items-center gap-2.5 px-3.5 py-2 rounded-xl glass border border-white/50">
                    <User className="w-3.5 h-3.5 text-primary" />
                    <span className="text-xs font-medium">{user.username}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="p-2.5 rounded-xl hover:bg-destructive/10 hover:text-destructive text-muted-foreground transition-colors"
                    title="Sign out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setAuthModalOpen(true)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium shadow-glow hover:shadow-lg transition-shadow"
                >
                  <Sparkles className="w-4 h-4" />
                  <span className="hidden sm:inline">Sign In</span>
                </motion.button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative z-10 p-3 pt-0 gap-3">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          currentChatId={currentChatId}
        />

        {/* Main View */}
        <main className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              <ChatInterface
                messages={messages}
                loading={loading}
                sendMessage={sendMessage}
                onNewLog={handleNewLog}
              />
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Audit Log Panel */}
        <AnimatePresence>
          {activeTab === 'chat' && !user && (
            <motion.aside
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
              className="hidden lg:block w-80 flex-shrink-0"
            >
              <div className="h-full glass-card rounded-2xl p-4 overflow-y-auto scrollbar-thin">
                <AuditLog logs={logs} />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* Auth Modal */}
      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
