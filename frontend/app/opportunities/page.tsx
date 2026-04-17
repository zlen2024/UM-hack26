'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { opportunities as opportunitiesApi, contacts as contactsApi } from '@/lib/api';
import { Plus, TrendingUp, DollarSign, Trash2, User } from 'lucide-react';

const STAGES = [
  { id: 'lead', label: 'Lead', color: 'bg-blue-500' },
  { id: 'qualified', label: 'Qualified', color: 'bg-cyan-500' },
  { id: 'proposal', label: 'Proposal', color: 'bg-purple-500' },
  { id: 'won', label: 'Won', color: 'bg-green-500' },
  { id: 'lost', label: 'Lost', color: 'bg-red-500' },
];

export default function OpportunitiesPage() {
  const router = useRouter();
  const [opportunitiesList, setOpportunitiesList] = useState<any[]>([]);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    value: '',
    stage: 'lead',
    contact_id: '',
    expected_close_date: '',
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const [opps, contacts] = await Promise.all([
        opportunitiesApi.list(),
        contactsApi.list(),
      ]);
      setOpportunitiesList(opps.data);
      setContactsList(contacts.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await opportunitiesApi.create({
        ...formData,
        value: parseFloat(formData.value),
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      });
      setShowModal(false);
      setFormData({ title: '', value: '', stage: 'lead', contact_id: '', expected_close_date: '' });
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStageChange = async (id: number, newStage: string) => {
    try {
      await opportunitiesApi.updateStage(id, newStage);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await opportunitiesApi.delete(id);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const getStageOps = (stage: string) =>
    opportunitiesList.filter((opp) => opp.stage === stage);

  const getTotalValue = (stage: string) =>
    getStageOps(stage).reduce((sum, opp) => sum + parseFloat(opp.value || 0), 0);

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
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Opportunities</h1>
            <p className="text-slate-500">Sales Pipeline</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            Add Opportunity
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {STAGES.map((stage) => (
            <div key={stage.id} className="bg-slate-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${stage.color}`} />
                  <span className="font-medium text-slate-700">{stage.label}</span>
                </div>
                <span className="text-sm text-slate-500">{getStageOps(stage.id).length}</span>
              </div>
              <div className="text-lg font-bold text-slate-800 mb-4">
                ${getTotalValue(stage.id).toLocaleString()}
              </div>
              <div className="space-y-2">
                {getStageOps(stage.id).map((opp) => (
                  <div
                    key={opp.id}
                    className="bg-white rounded-lg p-3 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => router.push(`/opportunities/${opp.id}`)}
                  >
                    <div className="font-medium text-slate-800 text-sm">{opp.title}</div>
                    <div className="text-primary font-semibold text-sm">
                      ${parseFloat(opp.value || 0).toLocaleString()}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <select
                        value={opp.stage}
                        onChange={(e) => {
                          e.stopPropagation();
                          handleStageChange(opp.id, e.target.value);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs bg-slate-50 rounded px-2 py-1 border-none"
                      >
                        {STAGES.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.label}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(opp.id);
                        }}
                        className="text-red-400 hover:text-red-600"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Add Opportunity</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Value *</label>
                  <input
                    type="number"
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Stage</label>
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
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Contact</label>
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
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Expected Close Date</label>
                  <input
                    type="date"
                    value={formData.expected_close_date}
                    onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div className="flex gap-3">
                  <button type="button" onClick={() => setShowModal(false)} className="flex-1 btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" className="flex-1 btn-primary">
                    Save
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}