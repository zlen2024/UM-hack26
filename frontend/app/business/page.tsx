'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import DataTable, { TableColumn } from 'react-data-table-component';
import Sidebar from '@/components/Sidebar';
import { businessBackground as businessApi } from '@/lib/api';
import { dataTablePaginationOptions, dataTableStyles } from '@/lib/tableStyles';
import { Plus, Search, BookOpen, Trash2, Edit } from 'lucide-react';

type BusinessRow = {
  id: number;
  category: string;
  title: string;
  content: string;
  is_active: boolean;
  priority: number;
};

export default function BusinessBackgroundPage() {
  const router = useRouter();
  const [backgroundsList, setBackgroundsList] = useState<BusinessRow[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [activeBgId, setActiveBgId] = useState<number | null>(null);
  const [formData, setFormData] = useState({ category: '', title: '', content: '', is_active: true, priority: 0 });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadBackgrounds();
  }, [router, search]);

  const loadBackgrounds = async () => {
    try {
      const res = await businessApi.list(search || undefined);
      setBackgroundsList(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setModalMode('create');
    setActiveBgId(null);
    setFormData({ category: 'company', title: '', content: '', is_active: true, priority: 0 });
    setShowModal(true);
  };

  const openEditModal = (bg: BusinessRow) => {
    setModalMode('edit');
    setActiveBgId(bg.id);
    setFormData({
      category: bg.category || '',
      title: bg.title || '',
      content: bg.content || '',
      is_active: bg.is_active,
      priority: bg.priority || 0,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (modalMode === 'create') {
        await businessApi.create(formData);
      } else if (activeBgId !== null) {
        await businessApi.update(activeBgId, formData);
      }
      setShowModal(false);
      setFormData({ category: '', title: '', content: '', is_active: true, priority: 0 });
      setActiveBgId(null);
      loadBackgrounds();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await businessApi.delete(id);
      loadBackgrounds();
    } catch (err) {
      console.error(err);
    }
  };

  const columns = useMemo<TableColumn<BusinessRow>[]>(
    () => [
      {
        name: 'Title',
        selector: (row) => row.title,
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center">
              <BookOpen size={16} className="text-blue-700" />
            </div>
            <span className="font-semibold text-ink">{row.title}</span>
          </div>
        ),
      },
      {
        name: 'Category',
        selector: (row) => row.category || '',
        sortable: true,
        cell: (row) => <span className="text-muted capitalize">{row.category || '-'}</span>,
      },
      {
        name: 'Content Snippet',
        selector: (row) => row.content || '',
        cell: (row) => <span className="text-muted truncate max-w-xs">{row.content || '-'}</span>,
      },
      {
        name: 'Status',
        selector: (row) => (row.is_active ? 'Active' : 'Inactive'),
        sortable: true,
        cell: (row) => (
          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
            {row.is_active ? 'Active' : 'Inactive'}
          </span>
        ),
      },
      {
        name: 'Actions',
        cell: (row) => (
          <div className="flex justify-end gap-3">
            <button
              onClick={() => openEditModal(row)}
              className="text-muted hover:text-blue-700"
              aria-label="Edit background"
            >
              <Edit size={18} />
            </button>
            <button
              onClick={() => handleDelete(row.id)}
              className="text-muted hover:text-rose-600"
              aria-label="Delete background"
            >
              <Trash2 size={18} />
            </button>
          </div>
        ),
        width: '140px',
      },
    ],
    []
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
            <div className="page-kicker">Knowledge Base</div>
            <h1 className="page-title mt-2">Business Background</h1>
            <p className="text-muted mt-2">Manage your business context for the AI agent.</p>
          </div>
          <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Add Context
          </button>
        </div>

        <div className="card mb-6 flex flex-col md:flex-row md:items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
            <input
              type="text"
              placeholder="Search business context..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <div className="text-xs uppercase tracking-[0.2em] text-muted">
            {backgroundsList.length} total
          </div>
        </div>

        <div className="card">
          {backgroundsList.length === 0 ? (
            <div className="text-center py-10 text-muted">No business context found</div>
          ) : (
            <DataTable
              columns={columns}
              data={backgroundsList}
              pagination
              highlightOnHover
              customStyles={dataTableStyles}
              paginationComponentOptions={dataTablePaginationOptions}
            />
          )}
        </div>

        {showModal && (
          <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50">
            <div className="modal-panel p-6 w-full max-w-lg">
              <h2 className="text-xl font-semibold text-ink mb-4">
                {modalMode === 'create' ? 'Add Business Context' : 'Edit Business Context'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="input-field"
                    required
                  >
                    <option value="company">Company (Mission, Values, Story)</option>
                    <option value="products">Products / Services</option>
                    <option value="faqs">FAQs</option>
                    <option value="policies">Policies</option>
                    <option value="processes">Processes</option>
                    <option value="industry">Industry Knowledge</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Content *</label>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    className="input-field"
                    rows={6}
                    required
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    id="is_active"
                  />
                  <label htmlFor="is_active" className="text-sm font-semibold text-ink">Active (Use in AI Context)</label>
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