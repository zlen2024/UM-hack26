'use client';

import { useEffect, useState, useMemo, useRef } from 'react';
import { chatMessages } from '@/lib/api';
import { Search, User, Bot, Phone, MoreVertical, MessageSquare } from 'lucide-react';

function formatDistanceToNowSimple(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return `Just now`;
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h`;
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays}d`;
  
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

interface Message {
  id: number;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  sender: {
    name: string;
    phone: string;
  };
}

interface CustomerSession {
  sessionId: string;
  name: string;
  phone: string;
  lastMessage: Message;
  messages: Message[];
}

export default function ChatMessagesTab() {
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const res = await chatMessages.list();
      // Sort messages chronologically (oldest first) so they display correctly in chat
      const sorted = [...res.data].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      setAllMessages(sorted);
    } catch (error) {
      console.error('Failed to load chat messages:', error);
    } finally {
      setLoading(false);
    }
  };

  // Group messages by session
  const customerSessions = useMemo(() => {
    const sessionsMap = new Map<string, CustomerSession>();
    
    allMessages.forEach(msg => {
      // Don't create sessions for system messages unless they're the only ones
      if (!sessionsMap.has(msg.session_id)) {
        sessionsMap.set(msg.session_id, {
          sessionId: msg.session_id,
          name: msg.sender.name || 'Unknown Customer',
          phone: msg.sender.phone || 'No Phone',
          lastMessage: msg,
          messages: [msg]
        });
      } else {
        const session = sessionsMap.get(msg.session_id)!;
        session.messages.push(msg);
        // Update last message
        if (new Date(msg.created_at) > new Date(session.lastMessage.created_at)) {
          session.lastMessage = msg;
        }
        // Update name/phone if we get better data
        if (msg.role === 'user') {
          if (msg.sender.name && session.name === 'Unknown Customer') session.name = msg.sender.name;
          if (msg.sender.phone && session.phone === 'No Phone') session.phone = msg.sender.phone;
        }
      }
    });

    // Convert to array and sort by most recent message
    return Array.from(sessionsMap.values()).sort((a, b) => 
      new Date(b.lastMessage.created_at).getTime() - new Date(a.lastMessage.created_at).getTime()
    );
  }, [allMessages]);

  const filteredSessions = useMemo(() => {
    if (!searchTerm) return customerSessions;
    const term = searchTerm.toLowerCase();
    return customerSessions.filter(session => 
      session.name.toLowerCase().includes(term) ||
      session.phone.toLowerCase().includes(term) ||
      session.messages.some(m => m.content.toLowerCase().includes(term))
    );
  }, [customerSessions, searchTerm]);

  // Select first session by default if none selected
  useEffect(() => {
    if (!selectedSessionId && filteredSessions.length > 0) {
      setSelectedSessionId(filteredSessions[0].sessionId);
    }
  }, [filteredSessions, selectedSessionId]);

  // Scroll to bottom when session changes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [selectedSessionId, allMessages]);

  const selectedSession = useMemo(() => 
    customerSessions.find(s => s.sessionId === selectedSessionId),
  [customerSessions, selectedSessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-500 flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <div>Loading chat messages...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
      <div className="flex h-full">
        
        {/* Left Sidebar - Customer List */}
        <div className="w-80 border-r border-slate-200 flex flex-col bg-white shrink-0">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <MessageSquare size={18} className="text-blue-600" />
              Chats
            </h2>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search chats..."
                className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-sm"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {filteredSessions.length === 0 ? (
              <div className="p-6 text-center text-sm text-slate-500">
                No conversations found.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {filteredSessions.map((session) => (
                  <button
                    key={session.sessionId}
                    onClick={() => setSelectedSessionId(session.sessionId)}
                    className={`w-full p-3 text-left transition-colors hover:bg-slate-50 flex items-start gap-3 ${
                      selectedSessionId === session.sessionId ? 'bg-blue-50/80 hover:bg-blue-50/80' : ''
                    }`}
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 text-blue-700 flex items-center justify-center shrink-0 font-semibold shadow-sm border border-blue-200/50">
                      {session.name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0 overflow-hidden">
                      <div className="flex justify-between items-baseline mb-1">
                        <h3 className="font-semibold text-slate-900 text-sm truncate pr-2">
                          {session.name}
                        </h3>
                        <span className="text-[11px] text-slate-500 shrink-0">
                          {formatDistanceToNowSimple(session.lastMessage.created_at)}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 truncate flex items-center gap-1">
                        {session.lastMessage.role === 'assistant' && (
                          <Bot size={10} className="shrink-0" />
                        )}
                        <span className="truncate">
                          {session.lastMessage.content}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Area - Chat Interface */}
        <div className="flex-1 flex flex-col bg-[#F8FAFC]">
          {selectedSession ? (
            <>
              {/* Chat Header */}
              <div className="h-16 px-6 border-b border-slate-200 bg-white flex items-center justify-between shrink-0 shadow-sm z-10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 text-blue-700 flex items-center justify-center font-semibold border border-blue-200/50">
                    {selectedSession.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 leading-tight">{selectedSession.name}</h3>
                    <div className="text-xs text-slate-500 flex items-center gap-1">
                      <Phone size={10} />
                      {selectedSession.phone}
                    </div>
                  </div>
                </div>
                <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors">
                  <MoreVertical size={18} />
                </button>
              </div>

              {/* Chat Messages */}
              <div 
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-6 custom-scrollbar"
                style={{ backgroundImage: 'radial-gradient(#E2E8F0 1px, transparent 1px)', backgroundSize: '20px 20px' }}
              >
                <div className="space-y-4 max-w-3xl mx-auto flex flex-col">
                  {selectedSession.messages.filter(m => m.role !== 'system').map((msg, index) => {
                    const isUser = msg.role === 'user';
                    
                    // Add date separator if needed
                    const prevMsg = index > 0 ? selectedSession.messages[index - 1] : null;
                    const showDate = !prevMsg || new Date(msg.created_at).toDateString() !== new Date(prevMsg.created_at).toDateString();

                    return (
                      <div key={msg.id} className="flex flex-col w-full">
                        {showDate && (
                          <div className="flex justify-center my-4">
                            <span className="px-3 py-1 bg-white/80 backdrop-blur border border-slate-200 text-slate-500 text-[11px] font-medium rounded-full shadow-sm">
                              {new Date(msg.created_at).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
                            </span>
                          </div>
                        )}
                        
                        <div className={`flex w-full ${isUser ? 'justify-start' : 'justify-end'}`}>
                          <div className={`max-w-[75%] relative group ${isUser ? 'mr-auto' : 'ml-auto'}`}>
                            
                            <div className={`px-4 py-2.5 rounded-2xl shadow-sm text-sm whitespace-pre-wrap leading-relaxed ${
                              isUser 
                                ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm' 
                                : 'bg-blue-600 text-white rounded-tr-sm'
                            }`}>
                              {msg.content}
                            </div>
                            
                            <div className={`flex items-center gap-1 mt-1 text-[10px] ${
                              isUser ? 'justify-start text-slate-400 ml-1' : 'justify-end text-slate-400 mr-1'
                            }`}>
                              {formatTime(msg.created_at)}
                              {!isUser && (
                                <Bot size={10} className="ml-1 opacity-70" />
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 bg-[#F8FAFC]">
              <div className="w-16 h-16 rounded-full bg-white border border-slate-200 flex items-center justify-center mb-4 shadow-sm">
                <MessageSquare size={24} className="text-slate-300" />
              </div>
              <p className="text-lg font-medium text-slate-500">No Chat Selected</p>
              <p className="text-sm mt-1">Select a conversation from the left to view messages</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
