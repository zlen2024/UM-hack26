'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth } from '@/lib/api';
import { preloadUserData } from '@/lib/cache';
import { ArrowLeft } from 'lucide-react';

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
          <Link href="/" className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs uppercase tracking-[0.3em]">
            Kacip CRM
          </div>
          <h1 className="mt-6 text-4xl font-semibold leading-tight">
            Plan, close, and grow with clarity.
          </h1>
          <p className="mt-4 text-base text-white/80 max-w-md">
            Keep every deal moving with a workspace built for shared momentum, crisp insight, and measurable growth.
          </p>
        </div>
      </div>

      <div className="flex flex-col justify-center p-8 lg:p-12">
        <div className="max-w-md w-full mx-auto">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <span className="text-white font-bold text-2xl" style={{ fontFamily: 'serif' }}>K</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome back</h2>
            <p className="text-gray-600">Sign in to your Kacip CRM account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-indigo-800 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-gray-600">
              Don't have an account?{' '}
              <Link href="/register" className="text-blue-600 hover:text-blue-700 font-semibold">
                Sign up
              </Link>
            </p>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <Link href="/" className="text-gray-500 hover:text-gray-700 text-sm flex items-center justify-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Kacip CRM
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}