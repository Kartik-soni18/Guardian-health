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
  const { user, logout } = useAuth();

  const addLog = (log) => {
    setLogs(prev => [log, ...prev]);
  };

  const handleSelectChat = (chatId) => {
    setCurrentChatId(chatId);
  };

  const handleNewChat = () => {
    setCurrentChatId(null);
  };

  return (
    <div className="app-container">
      {user && (
        <Sidebar 
          currentChatId={currentChatId} 
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
        />
      )}
      
      <main className="main-content">
        <header>
          <div className="logo">GuardianHealth</div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <span>Secure Health Agent</span>
              <span>•</span>
              <span>v3.0 Mongo</span>
            </div>
            
            <div className="user-menu" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              {user ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <button 
                    onClick={logout}
                    style={{ 
                      background: 'rgba(255,255,255,0.05)', 
                      border: '1px solid var(--glass-border)', 
                      color: 'white', 
                      padding: '0.4rem 0.8rem', 
                      borderRadius: '8px',
                      fontSize: '0.8rem',
                      cursor: 'pointer'
                    }}
                  >
                    Logout
                  </button>
                </div>
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
                    cursor: 'pointer'
                  }}
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </header>
        
        <div className="main-layout" style={{ gridTemplateColumns: user ? '1fr 300px' : '1fr' }}>
          <ChatInterface 
            onNewLog={addLog} 
            chatId={currentChatId}
            onChatStarted={(id) => setCurrentChatId(id)}
          />
          {!user && <AuditLog logs={logs} />}
        </div>

        <footer style={{ marginTop: '2rem', padding: '2rem 0', textAlign: 'center', fontSize: '0.75rem', color: '#475569', borderTop: '1px solid var(--glass-border)' }}>
          &copy; 2024 GuardianHealth Portfolio • v3.0 MongoDB Persistence
        </footer>
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
