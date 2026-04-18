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
          <div className="text-muted">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      <Sidebar />
      <div className="flex-1 p-6 lg:p-10">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => router.push('/contacts')} className="p-2 hover:bg-wash rounded-xl">
            <ArrowLeft size={20} className="text-muted" />
          </button>
          <div className="flex-1">
            <div className="page-kicker">Contact Profile</div>
            <h1 className="page-title mt-2">{contact?.name}</h1>
          </div>
          {editMode ? (
            <button onClick={handleSave} className="btn-primary flex items-center gap-2">
              <Save size={18} />
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
            <div className="card card-elevated">
              <h2 className="text-xl font-semibold text-ink mb-4">Contact Details</h2>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <User size={20} className="text-muted" />
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-ink">{contact?.name}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Mail size={20} className="text-muted" />
                  {editMode ? (
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-ink">{contact?.email || '-'}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Phone size={20} className="text-muted" />
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-ink">{contact?.phone || '-'}</span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Building size={20} className="text-muted" />
                  {editMode ? (
                    <input
                      type="text"
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <span className="text-ink">{contact?.company || '-'}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="card card-elevated">
              <h2 className="text-xl font-semibold text-ink mb-4">Notes</h2>
              {editMode ? (
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="input-field"
                  rows={4}
                />
              ) : (
                <p className="text-muted">{contact?.notes || 'No notes'}</p>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="card card-elevated">
              <h2 className="text-xl font-semibold text-ink mb-4">Activity</h2>
              {activities.length === 0 ? (
                <p className="text-muted text-sm">No activity yet</p>
              ) : (
                <div className="space-y-3">
                  {activities.map((activity) => (
                    <div key={activity.id} className="rounded-2xl bg-wash px-3 py-2">
                      <p className="text-sm font-semibold text-ink capitalize">{activity.type}</p>
                      <p className="text-xs text-muted">{activity.description}</p>
                      <p className="text-xs text-muted">
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