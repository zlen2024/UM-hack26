'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { googleCalendar, whatsapp } from '@/lib/api';
import { User, Mail, Calendar, CheckCircle2, XCircle, Zap, Cloud, ShieldCheck, MessageSquare } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [calendarTestEmail, setCalendarTestEmail] = useState(
    'fakhrulhakimy93@gmail.com'
  );
  const [calendarOAuth, setCalendarOAuth] = useState({
    configured: false,
    authorized: false,
  });
  const [calendarTestStatus, setCalendarTestStatus] = useState<null | string>(null);
  // Integration connection state
  const [integrationStatus, setIntegrationStatus] = useState({
    email: false,
    calendar: false,
    zapier: false,
    cloud: false,
    sso: false,
    whatsapp: false,
  });
  const [activeIntegration, setActiveIntegration] = useState<null | string>(null);
  const [integrationFields, setIntegrationFields] = useState<any>({});
  const [whatsappConfig, setWhatsappConfig] = useState<any>(null);
  
  // Neonize State
  const [neonizeStatus, setNeonizeStatus] = useState<any>({
    started: false,
    connected: false,
    has_qr: false,
    qr_code: null,
    phone_number: null
  });
  const [showNeonizeModal, setShowNeonizeModal] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadSettings = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/');
        return;
      }
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }

      const baseStatus = {
        email: localStorage.getItem('integration_email') === 'on',
        calendar: false,
        zapier: localStorage.getItem('integration_zapier') === 'on',
        cloud: localStorage.getItem('integration_cloud') === 'on',
        sso: localStorage.getItem('integration_sso') === 'on',
        whatsapp: localStorage.getItem('integration_whatsapp') === 'on',
      };
      if (isMounted) {
        setIntegrationStatus(baseStatus);
      }

      try {
        const response = await googleCalendar.status();
        if (isMounted) {
          setIntegrationStatus((prev) => ({
            ...prev,
            calendar: Boolean(response.data?.connected),
          }));
          setCalendarTestEmail(
            response.data?.test_email || 'fakhrulhakimy93@gmail.com'
          );
          setCalendarOAuth({
            configured: Boolean(response.data?.oauth_configured),
            authorized: Boolean(response.data?.authorized),
          });
        }
      } catch (error) {
        console.error('Failed to load Google Calendar status', error);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadSettings();

    const checkWhatsAppStatus = async () => {
      const storedPhoneId = localStorage.getItem('whatsapp_phone_number_id');
      if (storedPhoneId) {
        try {
          const response = await whatsapp.getConfig(storedPhoneId);
          if (response.data) {
            setWhatsappConfig(response.data);
            localStorage.setItem('integration_whatsapp', 'on');
            setIntegrationStatus((prev) => ({ ...prev, whatsapp: true }));
          }
        } catch (error) {
          localStorage.removeItem('whatsapp_phone_number_id');
          localStorage.setItem('integration_whatsapp', 'off');
        }
      }
    };
    checkWhatsAppStatus();
    
    // Check Neonize Status
    const checkNeonizeStatus = async () => {
      const userData = localStorage.getItem('user');
      if (userData) {
        const user = JSON.parse(userData);
        try {
          const res = await whatsapp.neonizeStatus(user.id);
          setNeonizeStatus(res.data);
        } catch(e) {
          console.error("Neonize status error", e);
        }
      }
    };
    checkNeonizeStatus();

    return () => {
      isMounted = false;
    };
  }, [router]);

  // Polling for QR Code when modal is open
  useEffect(() => {
    let interval: any;
    if (showNeonizeModal && !neonizeStatus.connected) {
      interval = setInterval(async () => {
        if (user?.id) {
          try {
            const res = await whatsapp.neonizeStatus(user.id);
            setNeonizeStatus(res.data);
            if (res.data.connected) {
              setShowNeonizeModal(false);
            }
          } catch(e) {}
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [showNeonizeModal, neonizeStatus.connected, user]);


  const handleConfigureEmail = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/gmail/oauth/authorize', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.authorization_url) {
          window.location.href = data.authorization_url;
        }
      } else {
        alert('Failed to get authorization URL');
      }
    } catch (err) {
      console.error(err);
      alert('Error connecting to Gmail');
    }
  };

  const handleConnect = (key: string) => {
    if (key === 'calendar' || key === 'email') {
      return;
    }
    setActiveIntegration(key);
    setIntegrationFields({});
  };

  const handleConnectGoogleCalendar = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/gmail/oauth/authorize', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.authorization_url) {
          console.log('[Settings] Redirecting to Google OAuth...');
          window.location.href = data.authorization_url;
        } else {
          alert('Authorization URL not received');
        }
      } else {
        alert('Failed to start OAuth');
      }
    } catch (err) {
      console.error('OAuth error:', err);
      alert('Error connecting to Google');
    }
  };

  const handleDisconnect = async (key: string) => {
    try {
      if (key === 'calendar') {
        await googleCalendar.clearCredentials();
      } else if (key === 'whatsapp') {
        localStorage.removeItem('whatsapp_phone_number_id');
      } else if (key === 'neonize') {
        if (user?.id) {
           await whatsapp.neonizeDisconnect(user.id);
           setNeonizeStatus({ started: false, connected: false, has_qr: false, qr_code: null, phone_number: null });
        }
        return;
      }
      localStorage.setItem(`integration_${key}`, 'off');
      setIntegrationStatus((prev) => ({ ...prev, [key]: false }));
      setActiveIntegration(null);
    } catch (error) {
      console.error('Failed to disconnect integration', error);
    }
  };

  const handleConnectNeonize = async () => {
    if (!user?.id) return;
    if (integrationStatus.whatsapp) {
      alert("You cannot have both WhatsApp Cloud API and Neonize connected at the same time. Please disconnect WhatsApp Bot first.");
      return;
    }
    try {
      setShowNeonizeModal(true); // show modal immediately to indicate loading
      const res = await whatsapp.neonizeStatus(user.id);
      if (!res.data.started) {
        await whatsapp.neonizeConnect();
      }
      setNeonizeStatus(res.data);
    } catch (e) {
      console.error('Failed to connect Neonize', e);
      alert('Failed to start WhatsApp connection');
      setShowNeonizeModal(false);
    }
  };

  const handleSaveIntegration = async (key: string, fields: any) => {
    try {
      if (key === 'calendar') {
        const testEmail =
          fields.testEmail || calendarTestEmail || 'fakhrulhakimy93@gmail.com';
        const rawJson = (fields.oauthJson || '').trim();
        if (!rawJson) {
          window.alert('OAuth credentials JSON is required.');
          return;
        }
        let oauthCredentials = null;
        try {
          oauthCredentials = JSON.parse(rawJson);
        } catch (error) {
          console.error('Invalid OAuth JSON', error);
          window.alert('Invalid OAuth credentials JSON.');
          return;
        }
        await googleCalendar.saveCredentials({
          oauth_credentials: oauthCredentials,
          test_email: testEmail,
        });
        setCalendarTestEmail(testEmail);
        const status = await googleCalendar.status();
        setIntegrationStatus((prev) => ({
          ...prev,
          calendar: Boolean(status.data?.connected),
        }));
        setCalendarOAuth({
          configured: Boolean(status.data?.oauth_configured),
          authorized: Boolean(status.data?.authorized),
        });
      } else if (key === 'whatsapp') {
        const userData = localStorage.getItem('user');
        const user = userData ? JSON.parse(userData) : null;
        if (!user?.id) {
          window.alert('User not found. Please login again.');
          return;
        }
        await whatsapp.createConfig({
          phone_number_id: fields.phone_number_id,
          display_phone_number: fields.display_phone_number,
          access_token: fields.access_token,
          app_secret: fields.app_secret || undefined,
          verify_token: fields.verify_token,
          user_id: user.id,
        });
        localStorage.setItem('whatsapp_phone_number_id', fields.phone_number_id);
        localStorage.setItem(`integration_${key}`, 'on');
        setIntegrationStatus((prev) => ({ ...prev, [key]: true }));
        setWhatsappConfig({
          phone_number_id: fields.phone_number_id,
          display_phone_number: fields.display_phone_number,
          user_id: user.id,
          has_app_secret: Boolean(fields.app_secret),
        });
      } else {
        localStorage.setItem(`integration_${key}`, 'on');
        setIntegrationStatus((prev) => ({ ...prev, [key]: true }));
      }
      setActiveIntegration(null);
    } catch (error) {
      console.error('Failed to save integration', error);
      window.alert('Failed to save integration. Check console for details.');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-muted">Loading...</div>
        </div>
      </div>
    );
  }

  const handleAuthorizeCalendar = async () => {
    try {
      const redirectUri = `${window.location.origin}/api/auth/callback/google`;
      const response = await googleCalendar.oauthAuthorize(redirectUri);
      const authUrl = response.data?.authorization_url;
      if (!authUrl) {
        window.alert('Authorization URL not received.');
        return;
      }
      window.location.assign(authUrl);
    } catch (error) {
      console.error('Failed to start OAuth', error);
      window.alert('Failed to start OAuth. Check console for details.');
    }
  };

  const handleTestCalendar = async () => {
    if (!calendarOAuth.authorized) {
      window.alert('Google Calendar is not authorized yet.');
      return;
    }
    try {
      setCalendarTestStatus('Sending test invite...');
      const start = new Date(Date.now() + 10 * 60 * 1000);
      const end = new Date(start.getTime() + 30 * 60 * 1000);
      await googleCalendar.createEvent({
        title: 'OAuth Test Event',
        description: 'Test event from UM CRM',
        start_time: start.toISOString(),
        end_time: end.toISOString(),
      });
      setCalendarTestStatus('Test event created. Check your calendar/inbox.');
    } catch (error) {
      console.error('Test event failed', error);
      setCalendarTestStatus('Test event failed. Check console for details.');
    }
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      <Sidebar />
      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-2xl p-6 lg:p-10">
          <div className="mb-8">
            <div className="page-kicker">Account</div>
            <h1 className="page-title mt-2">Settings</h1>
            <p className="text-muted mt-2">Manage your profile and connections.</p>
          </div>

          <div className="max-w-2xl space-y-6">
            <div className="card card-elevated">
              <h2 className="text-xl font-semibold text-ink mb-4">Profile</h2>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center shadow-soft">
                  <User size={30} className="text-white" />
                </div>
                <div>
                  <p className="font-semibold text-ink">{user?.full_name || 'User'}</p>
                  <p className="text-sm text-muted">{user?.email}</p>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Full Name</label>
                  <input
                    type="text"
                    defaultValue={user?.full_name || ''}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Email</label>
                  <input
                    type="email"
                    defaultValue={user?.email || ''}
                    className="input-field"
                    disabled
                  />
                </div>
              </div>
            </div>

            <div className="card card-elevated">
              <h2 className="text-xl font-semibold text-ink mb-4">Integrations</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <IntegrationBox
                  icon={<Mail size={22} className="text-blue-600" />}
                  name="Google Email"
                  desc="Sync your Gmail inbox and send emails from CRM."
                  status={integrationStatus.email ? 'on' : 'off'}
                  onConnect={handleConfigureEmail}
                  onDisconnect={() => handleDisconnect('email')}
                  customConnectText="Configure"
                />
                <IntegrationBox
                  icon={<Calendar size={22} className="text-blue-600" />}
                  name="Google Calendar"
                  desc="Sync events, meetings, and reminders."
                  status={integrationStatus.calendar ? 'on' : 'off'}
                  onConnect={handleConnectGoogleCalendar}
                  onDisconnect={() => handleDisconnect('calendar')}
                />
                <IntegrationBox
                  icon={<Zap size={22} className="text-amber-500" />}
                  name="Zapier"
                  desc="Automate workflows with 5000+ apps."
                  status={integrationStatus.zapier ? 'on' : 'off'}
                  onConnect={() => handleConnect('zapier')}
                  onDisconnect={() => handleDisconnect('zapier')}
                />
                <IntegrationBox
                  icon={<Cloud size={22} className="text-sky-500" />}
                  name="Cloud Storage"
                  desc="Attach and sync files from Google Drive."
                  status={integrationStatus.cloud ? 'on' : 'off'}
                  onConnect={() => handleConnect('cloud')}
                  onDisconnect={() => handleDisconnect('cloud')}
                />
                <IntegrationBox
                  icon={<MessageSquare size={22} className="text-green-600" />}
                  name="WhatsApp (QR Scan)"
                  desc="Unofficial: Connect via Neonize by scanning a QR code (security risks)."
                  status={neonizeStatus.connected ? 'on' : 'off'}
                  onConnect={handleConnectNeonize}
                  onDisconnect={() => handleDisconnect('neonize')}
                />
                <IntegrationBox
                  icon={<MessageSquare size={22} className="text-green-500" />}
                  name="WhatsApp Bot"
                  desc="Receive and reply to WhatsApp messages. Requires Cloud API."
                  status={integrationStatus.whatsapp ? 'on' : 'off'}
                  onConnect={() => handleConnect('whatsapp')}
                  onDisconnect={() => handleDisconnect('whatsapp')}
                />
              </div>
              {activeIntegration && (
                <IntegrationModal
                  key={activeIntegration}
                  type={activeIntegration}
                  onClose={() => setActiveIntegration(null)}
                  onSave={handleSaveIntegration}
                  fields={integrationFields}
                  setFields={setIntegrationFields}
                />
              )}
            </div>

            <div className="card card-elevated">
              <h2 className="text-xl font-semibold text-ink mb-2">Google Calendar Actions</h2>
              <p className="text-sm text-muted mb-4">
                Upload OAuth JSON, then authorize and send a test invite.
              </p>
              <div className="flex flex-col gap-3">
                <div className="flex flex-wrap gap-3">
                  <button
                    className="btn-primary"
                    onClick={handleAuthorizeCalendar}
                    disabled={!calendarOAuth.configured}
                  >
                    Authorize Google Calendar
                  </button>
                  <button
                    className="btn-ghost"
                    onClick={handleTestCalendar}
                    disabled={!calendarOAuth.authorized}
                  >
                    Send Test Invite
                  </button>
                </div>
                <div className="text-xs text-muted">
                  OAuth configured: {calendarOAuth.configured ? 'yes' : 'no'} · Authorized: {calendarOAuth.authorized ? 'yes' : 'no'}
                </div>
                {calendarTestStatus ? (
                  <div className="text-sm text-ink">{calendarTestStatus}</div>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {showNeonizeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="modal-panel w-full max-w-sm p-6 relative animate-fade-up text-center bg-white rounded-2xl shadow-xl">
            <button className="absolute top-3 right-3 text-muted hover:text-ink transition-colors" onClick={() => setShowNeonizeModal(false)}>
              <XCircle size={24} />
            </button>
            <h3 className="text-xl font-bold text-ink mb-2 flex items-center justify-center gap-2">
              <MessageSquare className="text-green-500" /> WhatsApp Pairing
            </h3>
            <p className="text-sm text-muted mb-6">Open WhatsApp on your phone, go to Linked Devices, and scan this QR code.</p>
            
            <div className="flex flex-col items-center justify-center min-h-[250px] bg-wash rounded-xl p-4 border border-slate-200">
              {neonizeStatus.has_qr && neonizeStatus.qr_code ? (
                <img src={neonizeStatus.qr_code} alt="WhatsApp QR Code" className="w-48 h-48 rounded-lg shadow-sm" />
              ) : neonizeStatus.connected ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle2 size={32} className="text-green-600" />
                  </div>
                  <p className="text-green-600 font-semibold">Successfully Connected!</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
                  <p className="text-sm text-muted">Generating QR code...</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --- IntegrationBox component ---
function IntegrationBox({ icon, name, desc, status, onConnect, onDisconnect, customConnectText }: {
  icon: React.ReactNode;
  name: string;
  desc: string;
  status: 'on' | 'off';
  onConnect: () => void;
  onDisconnect: () => void;
  customConnectText?: string;
}) {
  return (
    <div className="flex flex-col justify-between bg-wash rounded-2xl p-4 shadow-sm border border-transparent hover:border-blue-200 transition-all">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-11 h-11 bg-white rounded-xl flex items-center justify-center shadow-soft">
          {icon}
        </div>
        <div>
          <p className="font-semibold text-ink">{name}</p>
          <p className="text-xs text-muted mt-1">{desc}</p>
        </div>
      </div>
      <div className="flex items-center justify-between mt-2">
        <span className={`inline-flex items-center gap-1 text-xs font-semibold rounded-full px-2 py-1 ${status === 'on' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-muted'}`}>
          {status === 'on' ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {status === 'on' ? 'Enabled' : 'Disabled'}
        </span>
        {status === 'on' ? (
          <button className="btn-ghost text-xs font-semibold text-blue-700" onClick={onDisconnect}>Disconnect</button>
        ) : (
          <button className="btn-ghost text-xs font-semibold text-muted" onClick={onConnect}>{customConnectText || "Connect"}</button>
        )}
      </div>
    </div>
  );
}

// --- IntegrationModal ---
function IntegrationModal({ type, onClose, onSave, fields, setFields }: {
  type: string;
  onClose: () => void;
  onSave: (key: string, fields: any) => void;
  fields: any;
  setFields: (fields: any) => void;
}) {
  let label = '';
  let placeholder = '';
  let fieldKey = '';
  let fieldType: 'text' | 'textarea' = 'text';
  let secondaryLabel = '';
  let secondaryPlaceholder = '';
  let secondaryKey = '';
  if (type === 'email') {
    label = 'Email Address';
    placeholder = 'your@email.com';
    fieldKey = 'email';
  } else if (type === 'calendar') {
    label = 'OAuth Credentials JSON';
    placeholder = '{"web": {"client_id": "..."}}';
    fieldKey = 'oauthJson';
    fieldType = 'textarea';
    secondaryLabel = 'Test attendee email';
    secondaryPlaceholder = 'fakhrulhakimy93@gmail.com';
    secondaryKey = 'testEmail';
  } else if (type === 'zapier') {
    label = 'Zapier API Key';
    placeholder = 'zapier-api-key';
    fieldKey = 'apiKey';
  } else if (type === 'cloud') {
    label = 'Google Drive Email';
    placeholder = 'drive@email.com';
    fieldKey = 'driveEmail';
  } else if (type === 'sso') {
    label = 'SSO Provider ID';
    placeholder = 'provider-id';
    fieldKey = 'providerId';
  }

  if (type === 'whatsapp') {
    const webhookUrl = `${typeof window !== 'undefined' ? window.location.origin : ''}/api/whatsapp/webhook`;
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
        <div className="modal-panel w-full max-w-lg p-6 relative animate-fade-up max-h-[90vh] overflow-y-auto">
          <button className="absolute top-3 right-3 text-muted" onClick={onClose}>&times;</button>
          <h3 className="text-lg font-semibold text-ink mb-2">Configure WhatsApp Bot</h3>
          <p className="text-sm text-muted mb-4">Enter your WhatsApp Business API credentials below.</p>
          <form
            onSubmit={e => {
              e.preventDefault();
              onSave(type, fields);
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">Phone Number ID</label>
              <input
                className="input-field"
                type="text"
                placeholder="1067947496408186"
                value={fields.phone_number_id || ''}
                onChange={e => setFields({ ...fields, phone_number_id: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">Display Phone Number</label>
              <input
                className="input-field"
                type="text"
                placeholder="+1234567890"
                value={fields.display_phone_number || ''}
                onChange={e => setFields({ ...fields, display_phone_number: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">Access Token</label>
              <input
                className="input-field"
                type="text"
                placeholder="EAAZBKKZBYcZC7s..."
                value={fields.access_token || ''}
                onChange={e => setFields({ ...fields, access_token: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">Verify Token</label>
              <input
                className="input-field"
                type="text"
                placeholder="your_verify_token"
                value={fields.verify_token || ''}
                onChange={e => setFields({ ...fields, verify_token: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">App Secret <span className="text-xs text-muted font-normal">(optional — for webhook signature validation)</span></label>
              <input
                className="input-field"
                type="password"
                placeholder="your_meta_app_secret"
                value={fields.app_secret || ''}
                onChange={e => setFields({ ...fields, app_secret: e.target.value })}
              />
              <p className="text-xs text-muted mt-1">
                Found in your Meta App Dashboard → Settings → Basic → App Secret. Enables HMAC-SHA256 webhook validation.
              </p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <label className="block text-sm font-semibold text-ink mb-2">Webhook URL</label>
              <div className="flex items-center gap-2">
                <input
                  className="input-field text-sm flex-1"
                  type="text"
                  value={webhookUrl}
                  readOnly
                />
                <button
                  type="button"
                  className="btn-ghost text-xs whitespace-nowrap"
                  onClick={() => navigator.clipboard.writeText(webhookUrl)}
                >
                  Copy
                </button>
              </div>
              <p className="text-xs text-muted mt-2">
                Configure this URL in your Meta WhatsApp Cloud API webhook settings.
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
              <button type="submit" className="btn-primary">Save Configuration</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="modal-panel w-full max-w-md p-6 relative animate-fade-up">
        <button className="absolute top-3 right-3 text-muted" onClick={onClose}>&times;</button>
        <h3 className="text-lg font-semibold text-ink mb-2">Connect {type.charAt(0).toUpperCase() + type.slice(1)}</h3>
        <form
          onSubmit={e => {
            e.preventDefault();
            onSave(type, fields);
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-semibold text-ink mb-1">{label}</label>
            {fieldType === 'textarea' ? (
              <textarea
                className="input-field min-h-[140px]"
                placeholder={placeholder}
                value={fields[fieldKey] || ''}
                onChange={e => setFields({ ...fields, [fieldKey]: e.target.value })}
                required
              />
            ) : (
              <input
                className="input-field"
                type="text"
                placeholder={placeholder}
                value={fields[fieldKey] || ''}
                onChange={e => setFields({ ...fields, [fieldKey]: e.target.value })}
                required
              />
            )}
          </div>
          {secondaryKey ? (
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">
                {secondaryLabel}
              </label>
              <input
                className="input-field"
                type="email"
                placeholder={secondaryPlaceholder}
                value={fields[secondaryKey] || ''}
                onChange={e => setFields({ ...fields, [secondaryKey]: e.target.value })}
                required
              />
            </div>
          ) : null}
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary">Connect</button>
          </div>
        </form>
      </div>
    </div>
  );
}