import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTriage } from '../hooks/useTriage';

const Sidebar = ({ currentChatId, onSelectChat, onNewChat }) => {
  const [chats, setChats] = useState([]);
  const { user } = useAuth();
  const { getChats, deleteChat } = useTriage();
  const [loading, setLoading] = useState(false);

  const loadChats = async () => {
    if (!user) return;
    setLoading(true);
    const data = await getChats();
    if (data) {
      setChats(data);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadChats();
  }, [user, currentChatId]);

  if (!user) return null;

  return (
    <motion.aside 
      className="sidebar"
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      transition={{ type: 'spring', damping: 20 }}
    >
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <span className="plus-icon">+</span> New Chat
        </button>
      </div>

      <div className="chats-list">
        {loading && <div className="loader">Loading history...</div>}
        {!loading && chats.length === 0 && (
          <div className="no-chats">No previous chats</div>
        )}
        {chats.map((chat) => (
          <div 
            key={chat.chat_id} 
            className={`chat-item ${currentChatId === chat.chat_id ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.chat_id)}
          >
            <div className="chat-title">{chat.title}</div>
            <div className="chat-meta">
              <span className="chat-time">
                {new Date(chat.last_updated).toLocaleDateString()}
              </span>
              {chat.symptoms && chat.symptoms.length > 0 && (
                <span className="chat-tag">
                  {chat.symptoms[0]}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">{user.username[0].toUpperCase()}</div>
          <div className="username">@{user.username}</div>
        </div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
