import { useState, useCallback } from 'react';
import {
  Plus,
  MessageSquare,
  Trash2,
  Clock,
  AlertTriangle,
  X,
  Loader2,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { format } from 'date-fns';
import { Chat } from '@/types';
import { cn } from '@/lib/utils';

interface ChatSidebarProps {
  chats: Chat[];
  currentChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
  isLoading: boolean;
  isDeleting: boolean;
}

export function ChatSidebar({
  chats,
  currentChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  isLoading,
  isDeleting,
}: ChatSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleDelete = useCallback(
    (chatId: string) => {
      if (deleteConfirmId === chatId) {
        onDeleteChat(chatId);
        setDeleteConfirmId(null);
      } else {
        setDeleteConfirmId(chatId);
      }
    },
    [deleteConfirmId, onDeleteChat]
  );

  const handleNewChat = useCallback(() => {
    onNewChat();
    setSidebarOpen(false);
  }, [onNewChat]);

  const handleSelectChat = useCallback(
    (chatId: string) => {
      onSelectChat(chatId);
      setSidebarOpen(false);
    },
    [onSelectChat]
  );

  return (
    <>
      {/* Mobile Toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute left-4 top-20 z-30 rounded-lg border border-gray-200 bg-white p-2 shadow-sm md:hidden dark:border-gray-800 dark:bg-gray-900"
      >
        {sidebarOpen ? <X className="h-5 w-5" /> : <PanelLeft className="h-5 w-5" />}
      </button>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col border-r border-gray-200 bg-white transition-all duration-300 dark:border-gray-800 dark:bg-gray-950',
          collapsed ? 'w-0 md:w-16' : 'w-80',
          sidebarOpen
            ? 'fixed inset-y-0 left-0 z-30 w-80 md:relative md:inset-auto'
            : 'hidden md:flex'
        )}
      >
        {/* Header — height matches chat panel header */}
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-gray-200 px-4 dark:border-gray-800">
          {!collapsed && (
            <>
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Conversations
              </h2>
              <div className="flex items-center gap-1">
                <button
                  onClick={handleNewChat}
                  className="rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800"
                  title="New chat"
                >
                  <Plus className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setCollapsed(!collapsed)}
                  className="hidden rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 md:block"
                  title={collapsed ? 'Expand' : 'Collapse'}
                >
                  <PanelLeftClose className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
          {collapsed && (
            <button
              onClick={() => setCollapsed(false)}
              className="mx-auto rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            >
              <PanelLeft className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* New Chat Button (when collapsed) */}
        {collapsed && (
          <button
            onClick={handleNewChat}
            className="mx-auto mt-2 rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            title="New chat"
          >
            <Plus className="h-4 w-4" />
          </button>
        )}

        {/* Chat List */}
        {!collapsed && (
          <div className="flex-1 overflow-y-auto p-2">
            {isLoading && chats.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
              </div>
            ) : chats.length === 0 ? (
              <div className="py-8 text-center">
                <MessageSquare className="mx-auto mb-2 h-8 w-8 text-gray-300 dark:text-gray-700" />
                <p className="text-sm text-gray-500 dark:text-gray-500">
                  No conversations yet
                </p>
                <button
                  onClick={handleNewChat}
                  className="mt-2 text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400"
                >
                  Start a new chat
                </button>
              </div>
            ) : (
              <div className="space-y-1">
                {chats.map((chat) => {
                  const isActive = chat.id === currentChatId;
                  const isConfirming = deleteConfirmId === chat.id;

                  return (
                    <div
                      key={chat.id}
                      className={cn(
                        'group relative rounded-lg transition-colors',
                        isActive
                          ? 'bg-primary-50 dark:bg-primary-950/40'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-800/50'
                      )}
                    >
                      <button
                        onClick={() => handleSelectChat(chat.id)}
                        className="flex w-full items-start gap-3 px-3 py-2.5 text-left"
                      >
                        <MessageSquare
                          className={cn(
                            'mt-0.5 h-4 w-4 shrink-0',
                            isActive
                              ? 'text-primary-600 dark:text-primary-400'
                              : 'text-gray-400 dark:text-gray-600'
                          )}
                        />
                        <div className="min-w-0 flex-1">
                          <p
                            className={cn(
                              'truncate text-sm font-medium',
                              isActive
                                ? 'text-primary-900 dark:text-primary-100'
                                : 'text-gray-700 dark:text-gray-300'
                            )}
                          >
                            {chat.title || 'New Conversation'}
                          </p>
                          <div className="mt-0.5 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-600">
                            <Clock className="h-3 w-3" />
                            {format(new Date(chat.updatedAt), 'MMM d')}
                          </div>
                        </div>
                      </button>

                      {/* Delete Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(chat.id);
                        }}
                        disabled={isDeleting}
                        className={cn(
                          'absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 transition-all',
                          isConfirming
                            ? 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'
                            : 'opacity-0 group-hover:opacity-100 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-950 dark:hover:text-red-400',
                          isActive ? 'text-gray-400' : 'text-gray-400'
                        )}
                      >
                        {isDeleting && deleteConfirmId === chat.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="h-3.5 w-3.5" />
                        )}
                      </button>

                      {/* Delete Confirmation */}
                      {isConfirming && (
                        <div className="absolute inset-x-0 top-full z-10 mt-1 rounded-lg border border-red-200 bg-red-50 p-3 shadow-lg dark:border-red-900 dark:bg-red-950">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
                            <div>
                              <p className="text-xs font-medium text-red-900 dark:text-red-100">
                                Delete this conversation?
                              </p>
                              <div className="mt-2 flex gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDelete(chat.id);
                                  }}
                                  className="rounded-md bg-red-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-red-700"
                                >
                                  Delete
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setDeleteConfirmId(null);
                                  }}
                                  className="rounded-md border border-red-200 bg-white px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-50 dark:border-red-800 dark:bg-transparent dark:text-red-400"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Footer — padding matches chat input bar */}
        {!collapsed && (
          <div className="shrink-0 border-t border-gray-200/80 px-4 py-4 dark:border-gray-800">
            <button
              onClick={handleNewChat}
              className="flex w-full items-center gap-2 rounded-lg border border-dashed border-gray-300 px-3 py-2.5 text-sm text-gray-500 transition-colors hover:border-primary-400 hover:text-primary-600 dark:border-gray-700 dark:text-gray-500 dark:hover:border-primary-600 dark:hover:text-primary-400"
            >
              <Plus className="h-4 w-4" />
              New Conversation
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
