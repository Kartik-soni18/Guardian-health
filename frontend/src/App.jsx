import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import AuditLog from './components/AuditLog';
import AuthModal from './components/AuthModal';
import { AuthProvider, useAuth } from './context/AuthContext';

function AppContent() {
  const [logs, setLogs] = useState([]);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();

  const addLog = (log) => {
    setLogs(prev => [log, ...prev]);
  };

  const handleSelectChat = (chatId) => {
    setCurrentChatId(chatId);
    setSidebarOpen(false);
  };

  const handleNewChat = () => {
    setCurrentChatId(null);
    setSidebarOpen(false);
  };

  return (
    <div className="app-container">
      {/* Sidebar overlay for mobile */}
      {user && (
        <div
          className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {user && (
        <Sidebar
          currentChatId={currentChatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />
      )}

      <main className="main-content">
        <header>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* Hamburger — only visible on mobile when logged in */}
            {user && (
              <button
                className="hamburger-btn"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open menu"
              >
                <span />
                <span />
                <span />
              </button>
            )}
            <div className="logo">GuardianHealth</div>
          </div>

          <div className="header-right">
            {/* Persistent privacy badge */}
            <div className="header-privacy-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/>
              </svg>
              HIPAA Secure
            </div>

            {user ? (
              <button
                onClick={logout}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--glass-border)',
                  color: 'white',
                  padding: '0.4rem 0.85rem',
                  borderRadius: '8px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                Logout
              </button>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                style={{
                  background: 'var(--accent-primary)',
                  border: 'none',
                  color: 'white',
                  padding: '0.5rem 1.25rem',
                  borderRadius: '10px',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        <div className={`main-layout ${!user ? 'with-audit' : ''}`}>
          <ChatInterface
            onNewLog={addLog}
            chatId={currentChatId}
            onChatStarted={(id) => setCurrentChatId(id)}
          />
          {!user && <AuditLog logs={logs} />}
        </div>


      </main>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
