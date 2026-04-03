import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TriageResult from './TriageResult';
import PrivacyBadge from './PrivacyBadge';
import RejectedMessage from './RejectedMessage';
import ResearchOverview from './ResearchOverview';
import { useTriage } from '../hooks/useTriage';
import { useAuth } from '../context/AuthContext';

const ChatInterface = ({ onNewLog, chatId, onChatStarted }) => {
  const initialGreeting = {
    type: 'bot',
    text: "Hello, I'm Dr. Guardian. Please describe what you're experiencing.",
  };

  const [messages, setMessages] = useState([initialGreeting]);
  const [input, setInput] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const { getTriage, getChatHistory, loading } = useTriage();
  const { user } = useAuth();
  const scrollRef = useRef(null);
  const lastLoadedChatId = useRef(null);
  const inputRef = useRef(null);

  const loadHistory = useCallback(async (targetChatId) => {
    if (!targetChatId) {
      setMessages([initialGreeting]);
      setConversationHistory([]);
      lastLoadedChatId.current = null;
      return;
    }

    if (lastLoadedChatId.current === targetChatId) return;

    try {
      const history = await getChatHistory(targetChatId);
      if (history && history.length > 0) {
        const historyMessages = [];
        const historyContext = [];

        history.forEach(pair => {
          const { role, content } = pair;
          if (role === 'user') {
            historyMessages.push({ type: 'user', text: content });
            historyContext.push({ role: 'user', content });
          } else if (role === 'assistant') {
            const botObj = typeof content === 'string' ? { text: content } : content;
            historyMessages.push({ type: 'bot', ...botObj });
            historyContext.push({ role: 'assistant', content: botObj.text || 'Medical Analysis' });
          }
        });

        setMessages(historyMessages);
        setConversationHistory(historyContext);
        lastLoadedChatId.current = targetChatId;
      } else {
        setMessages([initialGreeting]);
        setConversationHistory([]);
        lastLoadedChatId.current = targetChatId;
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  }, [getChatHistory]);

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
    inputRef.current?.focus();

    setMessages(prev => [...prev, { type: 'user', text: userQuery }]);

    const updatedHistory = [
      ...conversationHistory,
      { role: 'user', content: userQuery },
    ];
    setConversationHistory(updatedHistory);

    try {
      const result = await getTriage(userQuery, chatId, updatedHistory);

      if (!result) {
        setMessages(prev => [...prev, { type: 'bot', text: 'I encountered an error. Please try again.' }]);
        return;
      }

      if (!chatId && result.chat_id) {
        lastLoadedChatId.current = result.chat_id;
        onChatStarted(result.chat_id);
      }

      let botMsg = { type: 'bot' };

      if (result.status === 'rejected') {
        botMsg = { type: 'rejected' };
      } else if (result.status === 'emergency') {
        botMsg = { ...botMsg, text: result.message, privacy: result.privacy, isEmergency: true };
      } else if (result.status === 'follow_up') {
        botMsg = { ...botMsg, text: result.message, privacy: result.privacy, isFollowUp: true, showForceButton: true };
      } else if (result.status === 'triage') {
        const triageData = result.triage || null;
        botMsg = {
          ...botMsg,
          triage: triageData,
          care: result.care || null,
          symptoms: result.symptoms,
          text: !triageData ? 'I was unable to complete the triage analysis. Please describe your symptoms in more detail.' : undefined,
          privacy: result.privacy,
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
        botMsg = { ...botMsg, triage: result.triage, research: result.research, privacy: result.privacy, compliance: result.compliance };
      }

      setMessages(prev => [...prev.filter(m => !m.isFollowUp), botMsg]);
      setConversationHistory(prev => [...prev, { role: 'assistant', content: botMsg.text || 'Medical Analysis' }]);
    } catch (err) {
      setMessages(prev => [...prev, { type: 'bot', text: 'Server communication error.' }]);
    }
  };

  const canSend = !loading && !!input.trim() && !!user;

  return (
    <div className="chat-window">
      <div className="messages-area" ref={scrollRef}>
        <AnimatePresence mode="popLayout">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.18 }}
              style={{
                alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '100%',
                width: msg.type === 'user' ? 'auto' : '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.type === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: '1rem',
              }}
            >
              {msg.type === 'user' && (
                <div className="bubble-user">{msg.text}</div>
              )}

              {msg.type === 'rejected' && <RejectedMessage />}

              {msg.type === 'bot' && (
                <div style={{ width: '100%' }}>
                  {msg.privacy && <PrivacyBadge privacy={msg.privacy} />}

                  {msg.text && (
                    <div className={`bubble-bot ${msg.isEmergency ? 'emergency' : msg.isFollowUp ? 'follow-up' : ''}`}>
                      {msg.text}
                      {msg.showForceButton && (
                        <div style={{ marginTop: '0.85rem', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '0.7rem' }}>
                          <button
                            onClick={() => setInput("That's it. Just give me results.")}
                            className="force-triage-btn"
                          >
                            Give me results with current information
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {msg.disease && <TriageResult disease={msg.disease} care={msg.care} symptoms={msg.symptoms} severity={msg.severity} />}
                  {msg.triage && <TriageResult triage={msg.triage} care={msg.care} symptoms={msg.symptoms} />}
                  {msg.research && <ResearchOverview research={msg.research} />}
                </div>
              )}
            </motion.div>
          ))}

          {loading && (
            <motion.div
              key="typing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="typing-indicator"
            >
              <div className="typing-dots">
                <span /><span /><span />
              </div>
              Dr. Guardian is analyzing…
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <form className="input-area" onSubmit={handleSend}>
        <div className="input-wrapper">
          <input
            ref={inputRef}
            autoFocus
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={user ? 'Describe your symptoms…' : 'Sign in to use GuardianHealth'}
            disabled={loading || !user}
          />

          <button type="submit" className="send-btn" disabled={!canSend} title="Send">
            {loading ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
            ) : (
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
