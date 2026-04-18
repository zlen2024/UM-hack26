'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { auth, users } from '@/lib/api';
import { User, Mail, Link, Calendar, Bell } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-muted">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      <Sidebar />
      <div className="flex-1 p-6 lg:p-10">
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
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-wash rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-soft">
                    <Mail size={20} className="text-muted" />
                  </div>
                  <div>
                    <p className="font-semibold text-ink">Email</p>
                    <p className="text-sm text-muted">Connect your email</p>
                  </div>
                </div>
                <button className="btn-ghost text-sm">Connect</button>
              </div>
              <div className="flex items-center justify-between p-4 bg-wash rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-soft">
                    <Calendar size={20} className="text-muted" />
                  </div>
                  <div>
                    <p className="font-semibold text-ink">Calendar</p>
                    <p className="text-sm text-muted">Sync with calendar</p>
                  </div>
                </div>
                <button className="btn-ghost text-sm">Connect</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}