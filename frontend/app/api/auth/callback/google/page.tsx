'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function GmailOAuthCallbackContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState<string>('Exchanging authorization code...');

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
        const token = localStorage.getItem('token');
        const response = await fetch('/api/gmail/oauth/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ code, state })
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Failed to complete OAuth');
        }

        setStatus('success');
        setMessage('Gmail authorization complete and watch started. You can return to Settings.');
      } catch (err: any) {
        console.error('OAuth complete failed', err);
        setStatus('error');
        setMessage(err.message || 'Failed to exchange code. Check console for details.');
      }
    };

    complete();
  }, [searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="card card-elevated w-full max-w-lg text-center">
        <h1 className="page-title">Google Email OAuth</h1>
        <p className="text-muted mt-3">{message}</p>
        {status === 'success' || status === 'error' ? (
          <a href="/settings" className="btn-primary mt-6 inline-flex">
            Back to Settings
          </a>
        ) : null}
      </div>
    </div>
  );
}

export default function GmailOAuthCallbackPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <GmailOAuthCallbackContent />
    </Suspense>
  );
}
