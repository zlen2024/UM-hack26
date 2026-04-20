'use client';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { MessageCircle, Bot } from 'lucide-react';

export default function WhatsAppPage() {
  const router = useRouter();

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center p-8 bg-white rounded-lg shadow-md max-w-md">
          <MessageCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">WhatsApp Integration</h2>
          <p className="text-gray-600 mb-6">Coming soon - Connect your WhatsApp Business account to manage conversations.</p>
          <button
            onClick={() => router.push('/whatsapp/agent-center')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Bot className="w-4 h-4" />
            Open Agent Center (Mockup)
          </button>
        </div>
      </div>
    </div>
  );
}