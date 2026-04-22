'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { LayoutDashboard, MessageSquare } from 'lucide-react';

export default function WhatsAppChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let interval: any;
    const fetchMessages = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          router.push('/');
          return;
        }

        const response = await api.get('/activities?type=whatsapp');
        // Filter and sort messages
        if (response.data && response.data.items) {
           const waMessages = response.data.items.filter((item: any) => item.type === 'whatsapp');
           setMessages(waMessages);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
    interval = setInterval(fetchMessages, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [router]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-ink">WhatsApp AI Conversations</h1>
        <button
          onClick={() => router.push('/settings')}
          className="btn-ghost flex items-center gap-2"
        >
          <LayoutDashboard size={18} />
          Back to Settings
        </button>
      </div>

      <div className="card card-elevated">
        <div className="space-y-4">
          {loading ? (
             <div className="flex justify-center p-8">
               <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
             </div>
          ) : messages.length === 0 ? (
            <div className="text-center p-8 text-muted">
              <MessageSquare size={48} className="mx-auto mb-4 opacity-50" />
              <p>No conversations yet. Messages handled by AI will appear here.</p>
            </div>
          ) : (
             messages.map((msg: any) => (
               <div key={msg.id} className="bg-wash p-4 rounded-xl shadow-sm">
                 <div className="flex justify-between items-start mb-2">
                   <div className="font-semibold text-ink">{msg.contact_name || 'Unknown Contact'}</div>
                   <div className="text-xs text-muted">
                     {new Date(msg.created_at).toLocaleString()}
                   </div>
                 </div>
                 <div className="text-sm text-ink bg-white p-3 rounded border border-slate-100 whitespace-pre-wrap">
                   {msg.content}
                 </div>
               </div>
             ))
          )}
        </div>
      </div>
    </div>
  );
}
