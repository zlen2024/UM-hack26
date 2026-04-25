'use client';

import { useEffect, useState } from 'react';
import { chatMessages } from '@/lib/api';
import { Search, User, Bot, Phone } from 'lucide-react';

function formatDistanceToNowSimple(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours} hours ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 30) return `${diffInDays} days ago`;
  
  return date.toLocaleDateString();
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

export default function ChatMessagesTab() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const res = await chatMessages.list();
      setMessages(res.data);
    } catch (error) {
      console.error('Failed to load chat messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredMessages = messages.filter((msg) => {
    const term = searchTerm.toLowerCase();
    return (
      msg.content.toLowerCase().includes(term) ||
      msg.sender.name.toLowerCase().includes(term) ||
      msg.sender.phone.toLowerCase().includes(term)
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-500">Loading chat messages...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Chat Messages</h2>
          <p className="text-slate-500 text-sm mt-1">
            Review the conversations between your agent and customers.
          </p>
        </div>

        <div className="relative w-72">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search messages, names, or phones..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        {filteredMessages.length === 0 ? (
          <div className="text-center text-slate-500 mt-10">
            No messages found.
          </div>
        ) : (
          <div className="space-y-4 pb-10">
            {filteredMessages.map((msg) => (
              <div
                key={msg.id}
                className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      msg.role === 'user' ? 'bg-indigo-100 text-indigo-600' : 'bg-emerald-100 text-emerald-600'
                    }`}>
                      {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900 text-sm flex items-center gap-2">
                        {msg.role === 'user' ? msg.sender.name : 'AI Agent'}
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-[10px] uppercase font-bold tracking-wider">
                          {msg.role}
                        </span>
                      </div>
                      {msg.role === 'user' && (
                        <div className="flex items-center gap-1 text-xs text-slate-500 mt-0.5">
                          <Phone size={12} />
                          {msg.sender.phone}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-slate-400 whitespace-nowrap">
                    {formatDistanceToNowSimple(msg.created_at)}
                  </div>
                </div>
                <div className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed pl-11">
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
