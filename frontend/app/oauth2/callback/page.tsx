'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { googleCalendar } from '@/lib/api';

export default function OAuthCallbackPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState<string>('Exchanging authorization code...');

  const redirectUri = useMemo(() => {
    if (typeof window === 'undefined') return '';
    return `${window.location.origin}/oauth2/callback`;
  }, []);

  useEffect(() => {
    const error = searchParams.get('error');
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    if (error) {
      setStatus('error');
      setMessage(`Authorization failed: ${error}`);
      return;
    }
    if (!code) {
      setStatus('error');
      setMessage('Missing authorization code.');
      return;
    }

    const complete = async () => {
      try {
        await googleCalendar.oauthComplete(code, redirectUri || undefined, state || undefined);
        setStatus('success');
        setMessage('Authorization complete. You can return to Settings.');
      } catch (err) {
        console.error('OAuth complete failed', err);
        setStatus('error');
        setMessage('Failed to exchange code. Check console for details.');
      }
    };

    complete();
  }, [searchParams, redirectUri]);

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="card card-elevated w-full max-w-lg text-center">
        <h1 className="page-title">Google Calendar OAuth</h1>
        <p className="text-muted mt-3">{message}</p>
        {status === 'success' ? (
          <a href="/settings" className="btn-primary mt-6 inline-flex">
            Back to Settings
          </a>
        ) : null}
      </div>
    </div>
  );
}
