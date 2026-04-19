'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { auth } from '@/lib/api';
import { preloadUserData } from '@/lib/cache';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await auth.login({ email, password });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      
      console.log('[Login] Login successful, starting background preload...');
      preloadUserData().then(() => {
        console.log('[Login] Preload complete, navigating to dashboard');
      });
      
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-[1.1fr,0.9fr]">
      <div className="relative hidden lg:flex flex-col justify-between p-12 text-white overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-indigo-800 to-sky-500" />
        <div className="absolute -top-24 -right-16 w-72 h-72 bg-white/20 rounded-full blur-3xl" />
        <div className="absolute bottom-10 -left-12 w-64 h-64 bg-white/15 rounded-full blur-3xl" />
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs uppercase tracking-[0.3em]">
            UM CRM
          </div>
          <h1 className="mt-6 text-4xl font-semibold leading-tight">
            Plan, close, and grow with clarity.
          </h1>
          <p className="mt-4 text-base text-white/80 max-w-md">
            Keep every deal moving with a workspace built for shared momentum, crisp insight,
            and calm focus.
          </p>
        </div>
        <div className="relative z-10 grid grid-cols-3 gap-4">
          {[
            { label: 'Pipeline', value: '140 deals' },
            { label: 'Contacts', value: '100+ people' },
            { label: 'Tasks', value: '180 actions' },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl bg-white/15 px-4 py-3">
              <div className="text-xs uppercase tracking-[0.25em] text-white/70">{item.label}</div>
              <div className="mt-1 text-lg font-semibold">{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md card card-elevated animate-fade-up">
          <div className="mb-6">
            <div className="page-kicker">Welcome back</div>
            <h1 className="page-title mt-2">Sign in</h1>
            <p className="text-muted mt-2">Access your shared CRM workspace.</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 text-rose-700 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-ink mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="••••••••"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-muted">
            Don&apos;t have an account?{' '}
            <a href="/register" className="font-semibold text-ink hover:underline">
              Register
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}