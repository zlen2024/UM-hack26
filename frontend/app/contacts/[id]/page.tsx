'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { contacts as contactsApi, activities as activitiesApi } from '@/lib/api';
import { User, Mail, Phone, Building, ArrowLeft, Save } from 'lucide-react';

export default function ContactDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = parseInt(params.id as string);
  const [contact, setContact] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', company: '', notes: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadContact();
  }, [router, id]);

  const loadContact = async () => {
    try {
      const [contactRes, activitiesRes] = await Promise.all([
        contactsApi.get(id),
        activitiesApi.list({ contact_id: id }),
      ]);
      setContact(contactRes.data);
      setActivities(activitiesRes.data);
      setFormData({
        name: contactRes.data.name || '',
        email: contactRes.data.email || '',
        phone: contactRes.data.phone || '',
        company: contactRes.data.company || '',
        notes: contactRes.data.notes || '',
      });
    } catch (err) {
      console.error(err);
      router.push('/contacts');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await contactsApi.update(id, formData);
      setEditMode(false);
      loadContact();
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

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => router.push('/contacts')} className="p-2 hover:bg-slate-200 rounded-lg">
            <ArrowLeft size={20} className="text-slate-600" />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-800">{contact?.name}</h1>
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
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Contact Details</h2>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <User size={20} className="text-slate-400" />
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-slate-800">{contact?.name}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Mail size={20} className="text-slate-400" />
                  {editMode ? (
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-slate-800">{contact?.email || '-'}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Phone size={20} className="text-slate-400" />
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-slate-800">{contact?.phone || '-'}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Building size={20} className="text-slate-400" />
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-slate-800">{contact?.company || '-'}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Notes</h2>
              {editMode ? (
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="input-field"
                  rows={4}
                />
              ) : (
                <p className="text-slate-600">{contact?.notes || 'No notes'}</p>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Activity</h2>
              {activities.length === 0 ? (
                <p className="text-slate-500 text-sm">No activity yet</p>
              ) : (
                <div className="space-y-3">
                  {activities.map((activity) => (
                    <div key={activity.id} className="border-l-2 border-primary pl-3">
                      <p className="text-sm font-medium text-slate-800 capitalize">{activity.type}</p>
                      <p className="text-xs text-slate-500">{activity.description}</p>
                      <p className="text-xs text-slate-400">
                        {new Date(activity.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}