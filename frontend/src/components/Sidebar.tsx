import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { useSidebar } from '@/hooks/useSidebar';
import {
  Plus,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Clock,
  Tag,
  LogOut,
  User,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  currentChatId: string | null;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  onNewChat,
  onSelectChat,
  currentChatId,
}) => {
  const { user, logout } = useAuth();
  const { chats, loading } = useSidebar();

  if (!user) return null;

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/10 backdrop-blur-sm z-30 lg:hidden"
            onClick={onToggle}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isOpen ? 300 : 0,
          opacity: isOpen ? 1 : 0,
        }}
        transition={{ duration: 0.35, ease: 'easeInOut' }}
        className="relative h-full z-10 overflow-hidden flex-shrink-0"
      >
        <div className="w-[300px] h-full flex flex-col glass-card rounded-2xl border border-white/60 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-white/40">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <MessageSquare className="w-4 h-4 text-primary" />
              </div>
              <span className="font-semibold text-sidebar-foreground text-sm">Conversations</span>
            </div>
            <button
              onClick={onToggle}
              className="p-1.5 rounded-lg text-sidebar-foreground/50 hover:text-sidebar-foreground hover:bg-white/50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onNewChat}
              className="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-primary/10 text-primary font-medium hover:bg-primary/20 transition-all border border-primary/20"
            >
              <Plus className="w-4 h-4" />
              <span>New Consultation</span>
            </motion.button>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto scrollbar-thin px-3 pb-3">
            {loading ? (
              <div className="space-y-2 mt-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 rounded-xl bg-white/40 animate-pulse" />
                ))}
              </div>
            ) : chats.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <MessageSquare className="w-10 h-10 text-sidebar-foreground/25 mb-3" />
                <p className="text-sm text-sidebar-foreground/50">No conversations yet</p>
                <p className="text-xs text-sidebar-foreground/30 mt-1">Start a new consultation</p>
              </div>
            ) : (
              <div className="space-y-1.5 mt-1">
                {chats.map((chat) => (
                  <motion.button
                    key={chat.id}
                    whileHover={{ scale: 1.01, x: 2 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => onSelectChat(chat.id)}
                    className={`w-full text-left p-3 rounded-xl transition-all border ${
                      currentChatId === chat.id
                        ? 'bg-primary/8 border-primary/25 shadow-sm'
                        : 'hover:bg-white/50 border-transparent'
                    }`}
                  >
                    <p className="text-sm font-medium text-sidebar-foreground truncate">
                      {chat.title || 'Untitled Conversation'}
                    </p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <Clock className="w-3 h-3 text-sidebar-foreground/35" />
                      <span className="text-xs text-sidebar-foreground/35">
                        {new Date(chat.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    {chat.symptom_tags && chat.symptom_tags.length > 0 && (
                      <div className="flex items-center gap-1 mt-2 flex-wrap">
                        {chat.symptom_tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-white/60 text-[10px] text-sidebar-foreground/55 border border-white/40"
                          >
                            <Tag className="w-2.5 h-2.5" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </motion.button>
                ))}
              </div>
            )}
          </div>

          {/* User Section */}
          <div className="p-3 border-t border-white/40">
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/40 border border-white/50">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 border border-primary/20">
                <User className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sidebar-foreground truncate">
                  {user.username}
                </p>
              </div>
              <button
                onClick={logout}
                className="p-1.5 rounded-lg text-sidebar-foreground/40 hover:text-destructive hover:bg-destructive/10 transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Toggle button when collapsed */}
      <AnimatePresence>
        {!isOpen && user && (
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            onClick={onToggle}
            className="absolute left-3 top-[76px] z-30 p-2.5 rounded-xl glass border border-white/60 shadow-glass hover:bg-white/70 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </motion.button>
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;
