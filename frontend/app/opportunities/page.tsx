'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import DataTable, { TableColumn } from 'react-data-table-component';
import Sidebar from '@/components/Sidebar';
import { opportunities as opportunitiesApi, contacts as contactsApi } from '@/lib/api';
import { dataTablePaginationOptions, dataTableStyles } from '@/lib/tableStyles';
import { Plus, Trash2, Edit, Eye, Search, TrendingUp, DollarSign, Calendar } from 'lucide-react';

const STAGES = [
  { id: 'lead', label: 'Lead', color: 'bg-blue-500' },
  { id: 'qualified', label: 'Qualified', color: 'bg-indigo-500' },
  { id: 'proposal', label: 'Proposal', color: 'bg-amber-500' },
  { id: 'won', label: 'Won', color: 'bg-blue-700' },
  { id: 'lost', label: 'Lost', color: 'bg-rose-500' },
];

type OpportunityRow = {
  id: number;
  title: string;
  value: number;
  stage: string;
  contact_id?: number | null;
  expected_close_date?: string | null;
};

export default function OpportunitiesPage() {
  const router = useRouter();
  const [opportunitiesList, setOpportunitiesList] = useState<OpportunityRow[]>([]);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [activeOppId, setActiveOppId] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('all');
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

  const contactsById = useMemo(() => {
    const map = new Map<number, string>();
    contactsList.forEach((contact: any) => map.set(contact.id, contact.name));
    return map;
  }, [contactsList]);

  const filteredOpportunities = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    return opportunitiesList.filter((opp) => {
      if (stageFilter !== 'all' && opp.stage !== stageFilter) return false;
      if (!normalized) return true;
      return opp.title.toLowerCase().includes(normalized);
    });
  }, [opportunitiesList, search, stageFilter]);

  const openCreateModal = () => {
    setModalMode('create');
    setActiveOppId(null);
    setFormData({ title: '', value: '', stage: 'lead', contact_id: '', expected_close_date: '' });
    setShowModal(true);
  };

  const openEditModal = (opp: OpportunityRow) => {
    setModalMode('edit');
    setActiveOppId(opp.id);
    setFormData({
      title: opp.title || '',
      value: opp.value ? String(opp.value) : '',
      stage: opp.stage || 'lead',
      contact_id: opp.contact_id ? String(opp.contact_id) : '',
      expected_close_date: opp.expected_close_date ? String(opp.expected_close_date) : '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        value: parseFloat(formData.value),
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      };
      if (modalMode === 'create') {
        await opportunitiesApi.create(payload);
      } else if (activeOppId !== null) {
        await opportunitiesApi.update(activeOppId, payload);
      }
      setShowModal(false);
      setActiveOppId(null);
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

  const columns = useMemo<TableColumn<OpportunityRow>[]>(
    () => [
      {
        name: 'Opportunity',
        selector: (row) => row.title,
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-50 rounded-full flex items-center justify-center">
              <TrendingUp size={16} className="text-blue-700" />
            </div>
            <div>
              <div className="font-semibold text-ink">{row.title}</div>
              <div className="text-xs text-muted uppercase tracking-[0.2em]">{row.stage}</div>
            </div>
          </div>
        ),
      },
      {
        name: 'Stage',
        selector: (row) => row.stage,
        sortable: true,
        cell: (row) => (
          <select
            value={row.stage}
            onChange={(e) => handleStageChange(row.id, e.target.value)}
            className="text-xs bg-white/80 rounded-lg px-2 py-1 border border-line"
          >
            {STAGES.map((stage) => (
              <option key={stage.id} value={stage.id}>
                {stage.label}
              </option>
            ))}
          </select>
        ),
        width: '160px',
      },
      {
        name: 'Value',
        selector: (row) => row.value,
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-2 text-ink">
            <DollarSign size={14} className="text-blue-700" />
            {Number(row.value || 0).toLocaleString()}
          </div>
        ),
        width: '150px',
      },
      {
        name: 'Close Date',
        selector: (row) => row.expected_close_date || '',
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-2 text-muted">
            <Calendar size={14} />
            {row.expected_close_date ? new Date(row.expected_close_date).toLocaleDateString() : '-'}
          </div>
        ),
        width: '160px',
      },
      {
        name: 'Contact',
        selector: (row) => (row.contact_id ? String(row.contact_id) : ''),
        cell: (row) => (
          <span className="text-muted">
            {row.contact_id ? contactsById.get(row.contact_id) || 'Unknown' : '-'}
          </span>
        ),
        width: '200px',
      },
      {
        name: 'Actions',
        cell: (row) => (
          <div className="flex justify-end gap-3">
            <button
              onClick={() => router.push(`/opportunities/${row.id}`)}
              className="text-muted hover:text-ink"
              aria-label="View opportunity"
            >
              <Eye size={18} />
            </button>
            <button
              onClick={() => openEditModal(row)}
              className="text-muted hover:text-blue-700"
              aria-label="Edit opportunity"
            >
              <Edit size={18} />
            </button>
            <button
              onClick={() => handleDelete(row.id)}
              className="text-muted hover:text-rose-600"
              aria-label="Delete opportunity"
            >
              <Trash2 size={18} />
            </button>
          </div>
        ),
        width: '140px',
      },
    ],
    [contactsById, router]
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
            <div className="page-kicker">Pipeline Focus</div>
            <h1 className="page-title mt-2">Opportunities</h1>
            <p className="text-muted mt-2">Stage, value, and close timing at a glance.</p>
          </div>
          <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Add Opportunity
          </button>
        </div>

        <div className="card mb-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
            <input
              type="text"
              placeholder="Search opportunities..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="input-field"
          >
            <option value="all">All stages</option>
            {STAGES.map((stage) => (
              <option key={stage.id} value={stage.id}>
                {stage.label}
              </option>
            ))}
          </select>
        </div>

        <div className="card">
          {filteredOpportunities.length === 0 ? (
            <div className="text-center py-10 text-muted">No opportunities found</div>
          ) : (
            <DataTable
              columns={columns}
              data={filteredOpportunities}
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
                {modalMode === 'create' ? 'Add Opportunity' : 'Edit Opportunity'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
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
                  <label className="block text-sm font-semibold text-ink mb-1">Value *</label>
                  <input
                    type="number"
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Stage</label>
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
                  <label className="block text-sm font-semibold text-ink mb-1">Contact</label>
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
                  <label className="block text-sm font-semibold text-ink mb-1">Expected Close Date</label>
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