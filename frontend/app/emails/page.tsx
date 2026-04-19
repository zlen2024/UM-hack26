'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { emails } from '@/lib/api';
import { Mail, RefreshCw, ChevronRight, ChevronDown, User, Clock, ArrowLeft } from 'lucide-react';

export default function EmailsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [emailList, setEmailList] = useState<any[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [gmailConnected, setGmailConnected] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/');
        return;
      }
      
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
        if (JSON.parse(userData).google_refresh_token) {
          setGmailConnected(true);
        }
      }

      await loadEmails();
      setLoading(false);
    };

    loadData();
  }, []);

  const loadEmails = async () => {
    try {
      const res = await emails.list({ limit: 50 });
      setEmailList(res.data);
    } catch (err: any) {
      if (err.response?.status === 400) {
        setGmailConnected(false);
      }
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await emails.sync();
      await loadEmails();
    } catch (err) {
      console.error('Sync failed:', err);
    }
    setSyncing(false);
  };

  const handleSelectEmail = async (email: any) => {
    try {
      const res = await emails.get(email.id);
      setSelectedEmail(res.data);
      if (!email.is_read) {
        await emails.markAsRead(email.id);
        setEmailList(emailList.map(e => 
          e.id === email.id ? { ...e, is_read: true } : e
        ));
      }
    } catch (err) {
      console.error('Failed to load email:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const parseFrom = (from: string) => {
    if (!from) return '';
    const match = from.match(/<(.+)>/);
    return match ? match[1] : from;
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!gmailConnected) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-8 bg-white rounded-lg shadow-md">
            <Mail className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Gmail Not Connected</h2>
            <p className="text-gray-600 mb-4">Connect your Gmail in Settings to view emails.</p>
            <button
              onClick={() => router.push('/settings')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to Settings
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      
      <div className="flex-1 flex">
        {/* Email List */}
        <div className={`${selectedEmail ? 'w-1/3' : 'w-full max-w-2xl'} border-r bg-white flex flex-col`}>
          <div className="p-4 border-b flex items-center justify-between">
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Emails
            </h1>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync'}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {emailList.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No emails yet. Click Sync to fetch emails.
              </div>
            ) : (
              emailList.map((email) => (
                <div
                  key={email.id}
                  onClick={() => handleSelectEmail(email)}
                  className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                    selectedEmail?.id === email.id ? 'bg-blue-50' : ''
                  } ${!email.is_read ? 'bg-blue-50/50' : ''}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {!email.is_read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full" />
                        )}
                        <p className="font-medium truncate">
                          {parseFrom(email.from)}
                        </p>
                      </div>
                      <p className="text-sm font-medium truncate">{email.subject || '(No subject)'}</p>
                      <p className="text-sm text-gray-500 truncate">{email.snippet}</p>
                    </div>
                    <p className="text-xs text-gray-400 whitespace-nowrap ml-2">
                      {formatDate(email.received_at)}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Email Detail */}
        {selectedEmail && (
          <div className="flex-1 flex flex-col">
            <div className="p-4 border-b flex items-center gap-2">
              <button
                onClick={() => setSelectedEmail(null)}
                className="p-2 hover:bg-gray-100 rounded-lg lg:hidden"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h2 className="text-lg font-semibold truncate">
                {selectedEmail.subject || '(No subject)'}
              </h2>
            </div>

            <div className="p-4 border-b bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                  {parseFrom(selectedEmail.from).charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="font-medium">{parseFrom(selectedEmail.from)}</p>
                  <p className="text-sm text-gray-500">
                    To: {selectedEmail.to}
                  </p>
                  <p className="text-sm text-gray-400">
                    {formatDate(selectedEmail.received_at)}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
              {selectedEmail.html_body ? (
                <div 
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: selectedEmail.html_body }}
                />
              ) : (
                <pre className="whitespace-pre-wrap text-sm">{selectedEmail.body || selectedEmail.snippet}</pre>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}