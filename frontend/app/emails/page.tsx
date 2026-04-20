'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { emails, gmail } from '@/lib/api';
import { Mail, RefreshCw, ChevronRight, ChevronDown, User, Clock, ArrowLeft, CheckCircle, XCircle, Sparkles, Lightbulb, Calendar, FileText, MessageSquare } from 'lucide-react';

export default function EmailsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [emailList, setEmailList] = useState<any[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailStatus, setGmailStatus] = useState<any>(null);

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
      }

      await loadGmailStatus();
      await loadEmails();
      setLoading(false);
    };

    loadData();
  }, []);

  const loadGmailStatus = async () => {
    try {
      const res = await gmail.status();
      setGmailStatus(res.data);
      setGmailConnected(res.data.connected);
    } catch (err) {
      console.error('Failed to load Gmail status:', err);
      setGmailConnected(false);
    }
  };

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
      <div className="flex h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading emails...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!gmailConnected) {
    return (
      <div className="flex h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 max-w-md">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Mail className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Gmail Not Connected</h2>
            <p className="text-gray-600 mb-6">Connect your Gmail account in Settings to start managing your emails.</p>
            <button
              onClick={() => router.push('/settings')}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 shadow-lg transition-all duration-200"
            >
              Go to Settings
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <Sidebar />
      <div className="flex-1 flex">
        {/* Email List */}
        <div className="w-1/3 border-r border-gray-200 bg-white/80 backdrop-blur-sm">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-gray-900">Emails</h1>
              <button
                onClick={handleSync}
                disabled={syncing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync'}
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {emailList.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Mail className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No emails found</p>
              </div>
            ) : (
              emailList.map((email) => (
                <div
                  key={email.id}
                  onClick={() => handleSelectEmail(email)}
                  className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-blue-50 transition-colors ${
                    selectedEmail?.id === email.id ? 'bg-blue-100' : ''
                  } ${!email.is_read ? 'bg-blue-50/50' : ''}`}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                      {parseFrom(email.from || '').charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className={`text-sm font-semibold truncate ${!email.is_read ? 'font-bold' : ''}`}>
                          {parseFrom(email.from || '')}
                        </p>
                        <span className="text-xs text-gray-500 flex-shrink-0">
                          {formatDate(email.received_at)}
                        </span>
                      </div>
                      <p className={`text-sm truncate mb-1 ${!email.is_read ? 'font-semibold' : 'text-gray-600'}`}>
                        {email.subject}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {email.snippet}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Email Detail */}
        <div className="flex-1 bg-white/80 backdrop-blur-sm">
          {selectedEmail ? (
            <div className="h-full flex flex-col">
              {/* Email Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h2 className="text-xl font-bold text-gray-900 mb-2">{selectedEmail.subject}</h2>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4" />
                        <span className="font-semibold">{parseFrom(selectedEmail.from)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>{formatDate(selectedEmail.received_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Email Content */}
              <div className="flex-1 flex">
                <div className="flex-1 p-6 overflow-y-auto">
                  <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: selectedEmail.body_html || selectedEmail.body_text || 'No content' }}
                  />
                </div>

                {/* AI Suggestions Sidebar */}
                <div className="w-80 border-l border-gray-200 bg-gradient-to-b from-blue-50 to-indigo-50 p-4">
                  <div className="bg-white rounded-xl p-4 shadow-lg border border-blue-100">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="w-5 h-5 text-blue-600" />
                      <h3 className="font-semibold text-gray-900">AI Suggestions</h3>
                    </div>

                    <div className="space-y-3">
                      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-blue-900">Priority Assessment</p>
                            <p className="text-xs text-blue-700 mt-1">
                              This appears to be a high-priority customer inquiry. Consider responding within 2 hours.
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-start gap-2">
                          <MessageSquare className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-green-900">Suggested Response</p>
                            <p className="text-xs text-green-700 mt-1">
                              "Thank you for your inquiry. I'd be happy to help you with this. Let me review your request and get back to you shortly."
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <div className="flex items-start gap-2">
                          <Calendar className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-purple-900">Next Steps</p>
                            <p className="text-xs text-purple-700 mt-1">
                              Schedule a follow-up call to discuss the details and create a proposal.
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <div className="flex items-start gap-2">
                          <FileText className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-orange-900">Action Items</p>
                            <ul className="text-xs text-orange-700 mt-1 space-y-1">
                              <li>• Review customer requirements</li>
                              <li>• Prepare pricing proposal</li>
                              <li>• Add to opportunity pipeline</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Mail className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Select an email</h3>
                <p className="text-gray-600">Choose an email from the list to view its contents</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}