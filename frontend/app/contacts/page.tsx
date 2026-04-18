'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import DataTable, { TableColumn } from 'react-data-table-component';
import Sidebar from '@/components/Sidebar';
import { contacts as contactsApi } from '@/lib/api';
import { dataTablePaginationOptions, dataTableStyles } from '@/lib/tableStyles';
import { Plus, Search, User, Mail, Phone, Building, Trash2, Edit, Eye } from 'lucide-react';

type ContactRow = {
  id: number;
  name: string;
  email?: string | null;
  phone?: string | null;
  company?: string | null;
  notes?: string | null;
};

export default function ContactsPage() {
  const router = useRouter();
  const [contactsList, setContactsList] = useState<ContactRow[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [activeContactId, setActiveContactId] = useState<number | null>(null);
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

  const openCreateModal = () => {
    setModalMode('create');
    setActiveContactId(null);
    setFormData({ name: '', email: '', phone: '', company: '', notes: '' });
    setShowModal(true);
  };

  const openEditModal = (contact: ContactRow) => {
    setModalMode('edit');
    setActiveContactId(contact.id);
    setFormData({
      name: contact.name || '',
      email: contact.email || '',
      phone: contact.phone || '',
      company: contact.company || '',
      notes: contact.notes || '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (modalMode === 'create') {
        await contactsApi.create(formData);
      } else if (activeContactId !== null) {
        await contactsApi.update(activeContactId, formData);
      }
      setShowModal(false);
      setFormData({ name: '', email: '', phone: '', company: '', notes: '' });
      setActiveContactId(null);
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

  const columns = useMemo<TableColumn<ContactRow>[]>(
    () => [
      {
        name: 'Name',
        selector: (row) => row.name,
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center">
              <User size={16} className="text-blue-700" />
            </div>
            <span className="font-semibold text-ink">{row.name}</span>
          </div>
        ),
      },
      {
        name: 'Email',
        selector: (row) => row.email || '',
        sortable: true,
        cell: (row) => <span className="text-muted">{row.email || '-'}</span>,
      },
      {
        name: 'Phone',
        selector: (row) => row.phone || '',
        sortable: true,
        cell: (row) => <span className="text-muted">{row.phone || '-'}</span>,
      },
      {
        name: 'Company',
        selector: (row) => row.company || '',
        sortable: true,
        cell: (row) => <span className="text-muted">{row.company || '-'}</span>,
      },
      {
        name: 'Actions',
        cell: (row) => (
          <div className="flex justify-end gap-3">
            <button
              onClick={() => router.push(`/contacts/${row.id}`)}
              className="text-muted hover:text-ink"
              aria-label="View contact"
            >
              <Eye size={18} />
            </button>
            <button
              onClick={() => openEditModal(row)}
              className="text-muted hover:text-blue-700"
              aria-label="Edit contact"
            >
              <Edit size={18} />
            </button>
            <button
              onClick={() => handleDelete(row.id)}
              className="text-muted hover:text-rose-600"
              aria-label="Delete contact"
            >
              <Trash2 size={18} />
            </button>
          </div>
        ),
        right: true,
        width: '140px',
      },
    ],
    [router]
  );

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
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-6">
          <div>
            <div className="page-kicker">CRM Directory</div>
            <h1 className="page-title mt-2">Contacts</h1>
            <p className="text-muted mt-2">Manage and search shared relationships.</p>
          </div>
          <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Add Contact
          </button>
        </div>

        <div className="card mb-6 flex flex-col md:flex-row md:items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
            <input
              type="text"
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <div className="text-xs uppercase tracking-[0.2em] text-muted">
            {contactsList.length} total
          </div>
        </div>

        <div className="card">
          {contactsList.length === 0 ? (
            <div className="text-center py-10 text-muted">No contacts found</div>
          ) : (
            <DataTable
              columns={columns}
              data={contactsList}
              pagination
              highlightOnHover
              customStyles={dataTableStyles}
              paginationComponentOptions={dataTablePaginationOptions}
            />
          )}
        </div>

        {showModal && (
          <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50">
            <div className="modal-panel p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-ink mb-4">
                {modalMode === 'create' ? 'Add Contact' : 'Edit Contact'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Phone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Company</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Notes</label>
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
                    {modalMode === 'create' ? 'Save' : 'Update'}
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