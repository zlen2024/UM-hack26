'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import DataTable, { TableColumn } from 'react-data-table-component';
import Sidebar from '@/components/Sidebar';
import { tasks as tasksApi, contacts as contactsApi } from '@/lib/api';
import { dataTablePaginationOptions, dataTableStyles } from '@/lib/tableStyles';
import { Plus, Trash2, Edit, Calendar, Flag, Eye, Search, CheckSquare } from 'lucide-react';

const STATUSES = [
  { id: 'pending', label: 'Pending', color: 'bg-slate-500' },
  { id: 'in_progress', label: 'In Progress', color: 'bg-sky-500' },
  { id: 'completed', label: 'Completed', color: 'bg-blue-600' },
];

const PRIORITIES = [
  { id: 'low', label: 'Low', color: 'text-slate-500' },
  { id: 'medium', label: 'Medium', color: 'text-amber-600' },
  { id: 'high', label: 'High', color: 'text-rose-600' },
];

type TaskRow = {
  id: number;
  title: string;
  description?: string | null;
  status: string;
  priority: string;
  due_date?: string | null;
  contact_id?: number | null;
};

export default function TasksPage() {
  const router = useRouter();
  const [tasksList, setTasksList] = useState<TaskRow[]>([]);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [activeTaskId, setActiveTaskId] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'pending',
    priority: 'medium',
    due_date: '',
    contact_id: '',
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
      const [tasks, contacts] = await Promise.all([
        tasksApi.list(),
        contactsApi.list(),
      ]);
      setTasksList(tasks.data);
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

  const filteredTasks = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    return tasksList.filter((task) => {
      if (statusFilter !== 'all' && task.status !== statusFilter) return false;
      if (priorityFilter !== 'all' && task.priority !== priorityFilter) return false;
      if (!normalized) return true;
      return (
        task.title.toLowerCase().includes(normalized) ||
        (task.description || '').toLowerCase().includes(normalized)
      );
    });
  }, [tasksList, search, statusFilter, priorityFilter]);

  const openCreateModal = () => {
    setModalMode('create');
    setActiveTaskId(null);
    setFormData({
      title: '',
      description: '',
      status: 'pending',
      priority: 'medium',
      due_date: '',
      contact_id: '',
    });
    setShowModal(true);
  };

  const openEditModal = (task: TaskRow) => {
    setModalMode('edit');
    setActiveTaskId(task.id);
    setFormData({
      title: task.title || '',
      description: task.description || '',
      status: task.status || 'pending',
      priority: task.priority || 'medium',
      due_date: task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : '',
      contact_id: task.contact_id ? String(task.contact_id) : '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      };
      if (modalMode === 'create') {
        await tasksApi.create(payload);
      } else if (activeTaskId !== null) {
        await tasksApi.update(activeTaskId, payload);
      }
      setShowModal(false);
      setActiveTaskId(null);
      setFormData({ title: '', description: '', status: 'pending', priority: 'medium', due_date: '', contact_id: '' });
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStatusChange = async (id: number, status: string) => {
    try {
      await tasksApi.updateStatus(id, status);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await tasksApi.delete(id);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const columns = useMemo<TableColumn<TaskRow>[]>(
    () => [
      {
        name: 'Task',
        selector: (row) => row.title,
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-50 rounded-full flex items-center justify-center">
              <CheckSquare size={16} className="text-blue-700" />
            </div>
            <div>
              <div className="font-semibold text-ink">{row.title}</div>
              {row.description && (
                <div className="text-xs text-muted line-clamp-1">{row.description}</div>
              )}
            </div>
          </div>
        ),
      },
      {
        name: 'Status',
        selector: (row) => row.status,
        sortable: true,
        cell: (row) => (
          <select
            value={row.status}
            onChange={(e) => handleStatusChange(row.id, e.target.value)}
            className="text-xs bg-white/80 rounded-lg px-2 py-1 border border-line"
          >
            {STATUSES.map((status) => (
              <option key={status.id} value={status.id}>
                {status.label}
              </option>
            ))}
          </select>
        ),
        width: '160px',
      },
      {
        name: 'Priority',
        selector: (row) => row.priority,
        sortable: true,
        cell: (row) => {
          const priority = PRIORITIES.find((p) => p.id === row.priority);
          return (
            <div className="flex items-center gap-2">
              <Flag size={14} className={priority?.color} />
              <span className="text-muted">{priority?.label || 'Medium'}</span>
            </div>
          );
        },
        width: '160px',
      },
      {
        name: 'Due',
        selector: (row) => row.due_date || '',
        sortable: true,
        cell: (row) => (
          <div className="flex items-center gap-2 text-muted">
            <Calendar size={14} />
            {row.due_date ? new Date(row.due_date).toLocaleDateString() : '-'}
          </div>
        ),
        width: '150px',
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
              onClick={() => router.push(`/tasks/${row.id}`)}
              className="text-muted hover:text-ink"
              aria-label="View task"
            >
              <Eye size={18} />
            </button>
            <button
              onClick={() => openEditModal(row)}
              className="text-muted hover:text-blue-700"
              aria-label="Edit task"
            >
              <Edit size={18} />
            </button>
            <button
              onClick={() => handleDelete(row.id)}
              className="text-muted hover:text-rose-600"
              aria-label="Delete task"
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
            <div className="page-kicker">Delivery Board</div>
            <h1 className="page-title mt-2">Tasks</h1>
            <p className="text-muted mt-2">Keep the team aligned on priority work.</p>
          </div>
          <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            Add Task
          </button>
        </div>

        <div className="card mb-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" size={18} />
            <input
              type="text"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field"
          >
            <option value="all">All statuses</option>
            {STATUSES.map((status) => (
              <option key={status.id} value={status.id}>
                {status.label}
              </option>
            ))}
          </select>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="input-field"
          >
            <option value="all">All priorities</option>
            {PRIORITIES.map((priority) => (
              <option key={priority.id} value={priority.id}>
                {priority.label}
              </option>
            ))}
          </select>
        </div>

        <div className="card">
          {filteredTasks.length === 0 ? (
            <div className="text-center py-10 text-muted">No tasks found</div>
          ) : (
            <DataTable
              columns={columns}
              data={filteredTasks}
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
                {modalMode === 'create' ? 'Add Task' : 'Edit Task'}
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
                  <label className="block text-sm font-semibold text-ink mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input-field"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="input-field"
                  >
                    {STATUSES.map((status) => (
                      <option key={status.id} value={status.id}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="input-field"
                  >
                    {PRIORITIES.map((priority) => (
                      <option key={priority.id} value={priority.id}>
                        {priority.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Due Date</label>
                  <input
                    type="datetime-local"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    className="input-field"
                  />
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