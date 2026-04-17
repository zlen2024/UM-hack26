'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { contacts as contactsApi } from '@/lib/api';
import { Plus, Search, User, Mail, Phone, Building, Trash2, Edit } from 'lucide-react';

export default function ContactsPage() {
  const router = useRouter();
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '', phone: '', company: '', notes: '' });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadContacts();
  }, [router, search]);

  const loadContacts = async () => {
    try {
      const res = await contactsApi.list(search || undefined);
      setContactsList(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await contactsApi.create(formData);
      setShowModal(false);
      setFormData({ name: '', email: '', phone: '', company: '', notes: '' });
      loadContacts();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await contactsApi.delete(id);
      loadContacts();
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
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Contacts</h1>
            <p className="text-slate-500">Manage your contacts</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            Add Contact
          </button>
        </div>

        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10"
            />
          </div>
        </div>

        <div className="card">
          {contactsList.length === 0 ? (
            <div className="text-center py-8 text-slate-500">No contacts found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Name</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Phone</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Company</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {contactsList.map((contact) => (
                    <tr key={contact.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                            <User size={16} className="text-primary" />
                          </div>
                          <span className="font-medium text-slate-800">{contact.name}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-600">{contact.email || '-'}</td>
                      <td className="py-3 px-4 text-slate-600">{contact.phone || '-'}</td>
                      <td className="py-3 px-4 text-slate-600">{contact.company || '-'}</td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => router.push(`/contacts/${contact.id}`)}
                          className="text-slate-400 hover:text-primary mr-3"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(contact.id)}
                          className="text-slate-400 hover:text-red-500"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Add Contact</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Company</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="input-field"
                    rows={3}
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