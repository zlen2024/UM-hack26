'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import KnowledgeGraphTab from '@/components/KnowledgeGraphTab';
import BusinessRulesTab from '@/components/BusinessRulesTab';
import ChatMessagesTab from '@/components/ChatMessagesTab';
import { Settings, Network, MessageSquare, BookOpen } from 'lucide-react';

export default function AgentManagerPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'kg' | 'messages' | 'rules'>('kg');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
    }
  }, [router]);

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-6 lg:px-10 py-6 shrink-0 z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
              <Settings size={20} />
            </div>
            <div>
              <div className="page-kicker">Administration</div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Agent Manager</h1>
            </div>
          </div>
          <p className="text-slate-500 text-sm mt-1 ml-13">Configure and monitor your AI agent's behavior and knowledge.</p>
          
          {/* Tabs Navigation */}
          <div className="flex gap-6 mt-8 border-b border-slate-200">
            <button
              onClick={() => setActiveTab('kg')}
              className={`pb-3 text-sm font-medium transition-colors relative flex items-center gap-2 ${
                activeTab === 'kg' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Network size={16} />
              Knowledge Graph
              {activeTab === 'kg' && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-t-full" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('messages')}
              className={`pb-3 text-sm font-medium transition-colors relative flex items-center gap-2 ${
                activeTab === 'messages' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <MessageSquare size={16} />
              Chat Messages
              {activeTab === 'messages' && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-t-full" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('rules')}
              className={`pb-3 text-sm font-medium transition-colors relative flex items-center gap-2 ${
                activeTab === 'rules' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <BookOpen size={16} />
              Business Rules
              {activeTab === 'rules' && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-t-full" />
              )}
            </button>
          </div>
        </header>

        {/* Tab Content */}
        <main className="flex-1 overflow-hidden p-6 lg:p-10">
          <div className="h-full bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="h-full p-6 overflow-y-auto">
              {activeTab === 'kg' && <KnowledgeGraphTab />}
              {activeTab === 'messages' && <ChatMessagesTab />}
              {activeTab === 'rules' && <BusinessRulesTab />}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
