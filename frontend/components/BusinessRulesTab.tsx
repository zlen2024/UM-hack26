'use client';

import { useEffect, useState } from 'react';
import { businessRules } from '@/lib/api';
import { Save, AlertCircle } from 'lucide-react';

export default function BusinessRulesTab() {
  const [rulesText, setRulesText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const res = await businessRules.get();
      setRulesText(res.data.rules_text || '');
    } catch (error) {
      console.error('Failed to load business rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMessage(null);
      await businessRules.update({ rules_text: rulesText });
      setSaveMessage({ type: 'success', text: 'Business rules saved successfully.' });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (error) {
      console.error('Failed to save business rules:', error);
      setSaveMessage({ type: 'error', text: 'Failed to save business rules. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-500">Loading business rules...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl h-full flex flex-col">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-slate-900">Business Rules</h2>
        <p className="text-slate-500 text-sm mt-1">
          Define the instructions, policies, and behavior guidelines for your AI agent.
          The agent will follow these rules when interacting with your customers.
        </p>
      </div>

      <div className="flex-1 flex flex-col gap-4 relative">
        <textarea
          value={rulesText}
          onChange={(e) => setRulesText(e.target.value)}
          placeholder="e.g. Always greet the user warmly. If a user asks for a refund, direct them to support@example.com."
          className="flex-1 w-full p-4 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm leading-relaxed text-slate-700 bg-slate-50/50"
        />

        <div className="flex items-center justify-between mt-2 shrink-0">
          <div className="flex items-center">
            {saveMessage && (
              <div className={`flex items-center gap-2 text-sm ${saveMessage.type === 'success' ? 'text-emerald-600' : 'text-rose-600'}`}>
                {saveMessage.type === 'error' && <AlertCircle size={16} />}
                {saveMessage.text}
              </div>
            )}
          </div>
          
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary flex items-center gap-2 px-6"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Rules'}
          </button>
        </div>
      </div>
    </div>
  );
}
