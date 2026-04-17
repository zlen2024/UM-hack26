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
          <div className="text-slate-500">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Settings</h1>
          <p className="text-slate-500">Manage your account</p>
        </div>

        <div className="max-w-2xl space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Profile</h2>
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
                <User size={32} className="text-white" />
              </div>
              <div>
                <p className="font-medium text-slate-800">{user?.full_name || 'User'}</p>
                <p className="text-sm text-slate-500">{user?.email}</p>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  defaultValue={user?.full_name || ''}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  defaultValue={user?.email || ''}
                  className="input-field"
                  disabled
                />
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Integrations</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                    <Mail size={20} className="text-slate-600" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-800">Email</p>
                    <p className="text-sm text-slate-500">Connect your email</p>
                  </div>
                </div>
                <button className="text-primary hover:underline text-sm">Connect</button>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                    <Calendar size={20} className="text-slate-600" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-800">Calendar</p>
                    <p className="text-sm text-slate-500">Sync with calendar</p>
                  </div>
                </div>
                <button className="text-primary hover:underline text-sm">Connect</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}