'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { googleCalendar } from '@/lib/api';
import { User, Mail, Calendar, CheckCircle2, XCircle, Zap, Cloud, ShieldCheck } from 'lucide-react';

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
  });
  const [activeIntegration, setActiveIntegration] = useState<null | string>(null);
  const [integrationFields, setIntegrationFields] = useState<any>({});

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
    return () => {
      isMounted = false;
    };
  }, [router]);


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
      }
      localStorage.setItem(`integration_${key}`, 'off');
      setIntegrationStatus((prev) => ({ ...prev, [key]: false }));
      setActiveIntegration(null);
    } catch (error) {
      console.error('Failed to disconnect integration', error);
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
      } else {
        localStorage.setItem(`integration_${key}`, 'on');
        setIntegrationStatus((prev) => ({ ...prev, [key]: true }));
      }
      setActiveIntegration(null);
    } catch (error) {
      console.error('Failed to save integration', error);
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
                  icon={<ShieldCheck size={22} className="text-green-600" />}
                  name="SSO / Security"
                  desc="Enable single sign-on and security features."
                  status={integrationStatus.sso ? 'on' : 'off'}
                  onConnect={() => handleConnect('sso')}
                  onDisconnect={() => handleDisconnect('sso')}
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