import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TriageResult from './TriageResult';
import PrivacyBadge from './PrivacyBadge';
import RejectedMessage from './RejectedMessage';
import ResearchOverview from './ResearchOverview';
import { useTriage } from '../hooks/useTriage';
import { useAuth } from '../context/AuthContext';

const ChatInterface = ({ onNewLog, chatId, onChatStarted }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const { getTriage, getChatHistory, loading } = useTriage();
  const { user } = useAuth();
  const scrollRef = useRef(null);
  const lastLoadedChatId = useRef(null);

  const initialGreeting = {
    type: 'bot',
    text: "Hello, I'm Dr. Guardian. Please describe what you're experiencing.",
  };

  const loadHistory = useCallback(async (targetChatId) => {
    if (!targetChatId) {
      setMessages([initialGreeting]);
      setConversationHistory([]);
      lastLoadedChatId.current = null;
      return;
    }

    // Only load if the ID has actually changed from what we last loaded
    if (lastLoadedChatId.current === targetChatId) return;

    try {
        const history = await getChatHistory(targetChatId);
        if (history && history.length > 0) {
            const historyMessages = [];
            const historyContext = [];
            
            history.forEach(pair => {
                const role = pair.role;
                const content = pair.content;
                
                if (role === 'user') {
                    historyMessages.push({ type: 'user', text: content });
                    historyContext.push({ role: 'user', content: content });
                } else if (role === 'assistant') {
                    // Safe handling of assistant content which might be an object
                    const botObj = typeof content === 'string' ? { text: content } : content;
                    historyMessages.push({ type: 'bot', ...botObj });
                    historyContext.push({ role: 'assistant', content: botObj.text || 'Medical Analysis' });
                }
            });

            setMessages(historyMessages);
            setConversationHistory(historyContext);
            lastLoadedChatId.current = targetChatId;
        } else {
            // New chat session
            setMessages([initialGreeting]);
            setConversationHistory([]);
            lastLoadedChatId.current = targetChatId;
        }
    } catch (err) {
        console.error("Failed to load chat history:", err);
    }
  }, [getChatHistory]);

  // Handle chatId changes (from mount or sidebar selection)
  useEffect(() => {
    if (chatId !== lastLoadedChatId.current) {
        loadHistory(chatId);
    }
  }, [chatId, loadHistory]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input;
    setInput('');
    
    // Add user message to UI immediately
    const userMsg = { type: 'user', text: userQuery };
    setMessages(prev => [...prev, userMsg]);

    const updatedHistory = [
      ...conversationHistory,
      { role: 'user', content: userQuery },
    ];
    setConversationHistory(updatedHistory);

    try {
        const result = await getTriage(userQuery, chatId, updatedHistory);

        if (!result) {
          setMessages(prev => [
            ...prev,
            { type: 'bot', text: 'I encountered an error. Please try again.' },
          ]);
          return;
        }

        // Assign chat_id if new
        if (!chatId && result.chat_id) {
           lastLoadedChatId.current = result.chat_id;
           onChatStarted(result.chat_id);
        }

        let botMsg = { type: 'bot' };
        if (result.status === 'rejected') {
          botMsg = { type: 'rejected' };
        } else if (result.status === 'follow_up') {
          botMsg = {
            ...botMsg,
            text: result.message,
            privacy: result.privacy,
            isFollowUp: true,
            showForceButton: true,
          };
        } else if (result.status === 'diagnosed') {
          botMsg = {
            ...botMsg,
            disease: result.disease,
            care: result.care,
            symptoms: result.symptoms,
            duration: result.duration,
            severity: result.severity,
            privacy: result.privacy,
            disclaimer: result.disclaimer,
          };
        } else {
          botMsg = {
            ...botMsg,
            triage: result.triage,
            research: result.research,
            privacy: result.privacy,
            compliance: result.compliance,
          };
        }

        // Add to UI
        setMessages(prev => [...prev.filter(m => !m.isFollowUp), botMsg]);
        setConversationHistory(prev => [...prev, { role: 'assistant', content: botMsg.text || 'Medical Analysis' }]);
    } catch (err) {
        setMessages(prev => [...prev, { type: 'bot', text: 'Server communication error.' }]);
    }
  };

  return (
    <div className="chat-window">
      <div className="messages-area" ref={scrollRef}>
        <AnimatePresence mode="popLayout">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.98, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              style={{
                alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start',
                maxWidth:  '100%',
                width:     'auto',
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.type === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '1rem'
              }}
            >
              {msg.type === 'user' && (
                <div style={{ background: 'var(--accent-primary)', padding: '0.8rem 1.2rem', borderRadius: '18px 18px 0 18px', color: 'white', maxWidth: '80%' }}>
                  {msg.text}
                </div>
              )}

              {msg.type === 'rejected' && <RejectedMessage />}

              {msg.type === 'bot' && (
                <div style={{ width: '100%', maxWidth: '90%' }}>
                  {msg.text && (
                    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem 1.25rem', borderRadius: '18px 18px 18px 0', border: '1px solid var(--glass-border)' }}>
                      {msg.text}
                      {msg.showForceButton && (
                         <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem' }}>
                            <button 
                                onClick={() => setInput("That's it. Just give me results.")} 
                                className="force-triage-btn"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-dim)', padding: '0.4rem 0.8rem', borderRadius: '8px', fontSize: '0.75rem', cursor: 'pointer' }}
                            >
                                Give me results with current information
                            </button>
                         </div>
                      )}
                    </div>
                  )}
                  {msg.privacy && <PrivacyBadge privacy={msg.privacy} />}
                  {msg.disease && <TriageResult disease={msg.disease} care={msg.care} symptoms={msg.symptoms} severity={msg.severity} />}
                  {msg.triage && <TriageResult triage={msg.triage} />}
                  {msg.research && <ResearchOverview research={msg.research} />}
                </div>
              )}
            </motion.div>
          ))}
          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ padding: '0.5rem', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
               Dr. Guardian is analyzing...
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <form className="input-area" onSubmit={handleSend}>
        <div className="input-wrapper">
          <input
            autoFocus
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={user ? "Describe your symptoms..." : "Sign in to use GuardianHealth"}
            disabled={loading || !user}
          />
          <button type="submit" className="send-btn" disabled={loading || !input.trim() || !user}>
            {loading ? '...' : (
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
