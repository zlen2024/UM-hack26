'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { opportunities as opportunitiesApi, contacts as contactsApi } from '@/lib/api';
import { ArrowLeft, Save, DollarSign, Calendar, User } from 'lucide-react';

const STAGES = [
  { id: 'lead', label: 'Lead', color: 'bg-blue-500' },
  { id: 'qualified', label: 'Qualified', color: 'bg-cyan-500' },
  { id: 'proposal', label: 'Proposal', color: 'bg-purple-500' },
  { id: 'won', label: 'Won', color: 'bg-green-500' },
  { id: 'lost', label: 'Lost', color: 'bg-red-500' },
];

export default function OpportunityDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = parseInt(params.id as string);
  const [opportunity, setOpportunity] = useState<any>(null);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    value: '',
    stage: 'lead',
    contact_id: '',
    expected_close_date: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadOpportunity();
  }, [router, id]);

  const loadOpportunity = async () => {
    try {
      const [oppRes, contactsRes] = await Promise.all([
        opportunitiesApi.get(id),
        contactsApi.list(),
      ]);
      setOpportunity(oppRes.data);
      setContactsList(contactsRes.data);
      setFormData({
        title: oppRes.data.title || '',
        value: oppRes.data.value || '',
        stage: oppRes.data.stage || 'lead',
        contact_id: oppRes.data.contact_id || '',
        expected_close_date: oppRes.data.expected_close_date || '',
      });
    } catch (err) {
      console.error(err);
      router.push('/opportunities');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await opportunitiesApi.update(id, {
        ...formData,
        value: parseFloat(formData.value),
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      });
      setEditMode(false);
      loadOpportunity();
    } catch (err) {
      console.error(err);
    }
  };

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

  const currentStage = STAGES.find((s) => s.id === opportunity?.stage);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => router.push('/opportunities')} className="p-2 hover:bg-slate-200 rounded-lg">
            <ArrowLeft size={20} className="text-slate-600" />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-800">{opportunity?.title}</h1>
          </div>
          {editMode ? (
            <button onClick={handleSave} className="btn-primary flex items-center gap-2">
              <Save size={20} />
              Save
            </button>
          ) : (
            <button onClick={() => setEditMode(true)} className="btn-primary">
              Edit
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Opportunity Details</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Title</label>
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <p className="text-slate-800">{opportunity?.title}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Value</label>
                  {editMode ? (
                    <input
                      type="number"
                      value={formData.value}
                      onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-2xl font-bold text-primary">
                      <DollarSign size={24} />
                      {parseFloat(opportunity?.value || 0).toLocaleString()}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Stage</label>
                  {editMode ? (
                    <select
                      value={formData.stage}
                      onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                      className="input-field"
                    >
                      {STAGES.map((stage) => (
                        <option key={stage.id} value={stage.id}>
                          {stage.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${currentStage?.color}`} />
                      <span className="text-slate-800">{currentStage?.label}</span>
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Contact</label>
                  {editMode ? (
                    <select
                      value={formData.contact_id}
                      onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
                      className="input-field"
                    >
                      <option value="">Select contact</option>
                      {contactsList.map((contact) => (
                        <option key={contact.id} value={contact.id}>
                          {contact.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-slate-800">
                      {opportunity?.contact_id
                        ? contactsList.find((c) => c.id === opportunity.contact_id)?.name || '-'
                        : '-'}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Expected Close Date</label>
                  {editMode ? (
                    <input
                      type="date"
                      value={formData.expected_close_date}
                      onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-slate-800">
                      <Calendar size={16} className="text-slate-400" />
                      {opportunity?.expected_close_date
                        ? new Date(opportunity.expected_close_date).toLocaleDateString()
                        : '-'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Status</h2>
              <div className="space-y-2">
                {STAGES.map((stage) => (
                  <div
                    key={stage.id}
                    className={`p-3 rounded-lg flex items-center gap-3 ${
                      opportunity?.stage === stage.id ? 'bg-slate-100' : 'bg-slate-50'
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full ${stage.color}`} />
                    <span className="text-slate-800">{stage.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}