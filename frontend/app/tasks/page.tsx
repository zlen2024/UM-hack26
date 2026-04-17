'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { tasks as tasksApi, contacts as contactsApi } from '@/lib/api';
import { Plus, Trash2, Edit, Calendar, Flag } from 'lucide-react';

const STATUSES = [
  { id: 'pending', label: 'Pending', color: 'bg-slate-500' },
  { id: 'in_progress', label: 'In Progress', color: 'bg-blue-500' },
  { id: 'completed', label: 'Completed', color: 'bg-green-500' },
];

const PRIORITIES = [
  { id: 'low', label: 'Low', color: 'text-slate-500' },
  { id: 'medium', label: 'Medium', color: 'text-amber-500' },
  { id: 'high', label: 'High', color: 'text-red-500' },
];

export default function TasksPage() {
  const router = useRouter();
  const [tasksList, setTasksList] = useState<any[]>([]);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await tasksApi.create({
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      });
      setShowModal(false);
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

  const getStatusTasks = (status: string) =>
    tasksList.filter((task) => task.status === status);

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
            <h1 className="text-2xl font-bold text-slate-800">Tasks</h1>
            <p className="text-slate-500">Manage your tasks</p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            Add Task
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {STATUSES.map((status) => (
            <div key={status.id} className="bg-slate-100 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${status.color}`} />
                  <span className="font-medium text-slate-700">{status.label}</span>
                </div>
                <span className="text-sm text-slate-500">{getStatusTasks(status.id).length}</span>
              </div>
              <div className="space-y-2">
                {getStatusTasks(status.id).map((task) => {
                  const priority = PRIORITIES.find((p) => p.id === task.priority);
                  return (
                    <div
                      key={task.id}
                      className="bg-white rounded-lg p-3 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => router.push(`/tasks/${task.id}`)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="font-medium text-slate-800 text-sm">{task.title}</div>
                        <Flag size={14} className={priority?.color} />
                      </div>
                      {task.description && (
                        <div className="text-slate-500 text-xs mt-1 line-clamp-2">
                          {task.description}
                        </div>
                      )}
                      {task.due_date && (
                        <div className="flex items-center gap-1 mt-2 text-xs text-slate-400">
                          <Calendar size={12} />
                          {new Date(task.due_date).toLocaleDateString()}
                        </div>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <select
                          value={task.status}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleStatusChange(task.id, e.target.value);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs bg-slate-50 rounded px-2 py-1 border-none"
                        >
                          {STATUSES.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.label}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(task.id);
                          }}
                          className="text-red-400 hover:text-red-600"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Add Task</h2>
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
                  <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input-field"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
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
                  <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
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
                  <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
                  <input
                    type="datetime-local"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    className="input-field"
                  />
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