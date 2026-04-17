'use client';
import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { tasks as tasksApi, contacts as contactsApi } from '@/lib/api';
import { ArrowLeft, Save, Calendar, Flag, CheckSquare } from 'lucide-react';

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

export default function TaskDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = parseInt(params.id as string);
  const [task, setTask] = useState<any>(null);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'pending',
    priority: 'medium',
    due_date: '',
    contact_id: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadTask();
  }, [router, id]);

  const loadTask = async () => {
    try {
      const [taskRes, contactsRes] = await Promise.all([
        tasksApi.get(id),
        contactsApi.list(),
      ]);
      setTask(taskRes.data);
      setContactsList(contactsRes.data);
      setFormData({
        title: taskRes.data.title || '',
        description: taskRes.data.description || '',
        status: taskRes.data.status || 'pending',
        priority: taskRes.data.priority || 'medium',
        due_date: taskRes.data.due_date?.slice(0, 16) || '',
        contact_id: taskRes.data.contact_id || '',
      });
    } catch (err) {
      console.error(err);
      router.push('/tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await tasksApi.update(id, {
        ...formData,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        contact_id: formData.contact_id ? parseInt(formData.contact_id) : null,
      });
      setEditMode(false);
      loadTask();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStatusChange = async (status: string) => {
    try {
      await tasksApi.updateStatus(id, status);
      loadTask();
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

  const currentStatus = STATUSES.find((s) => s.id === task?.status);
  const currentPriority = PRIORITIES.find((p) => p.id === task?.priority);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => router.push('/tasks')} className="p-2 hover:bg-slate-200 rounded-lg">
            <ArrowLeft size={20} className="text-slate-600" />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-800">{task?.title}</h1>
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
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Task Details</h2>
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
                    <p className="text-slate-800">{task?.title}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Description</label>
                  {editMode ? (
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="input-field"
                      rows={4}
                    />
                  ) : (
                    <p className="text-slate-600">{task?.description || 'No description'}</p>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-500 mb-1">Status</label>
                    {editMode ? (
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
                    ) : (
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${currentStatus?.color}`} />
                        <span className="text-slate-800">{currentStatus?.label}</span>
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-500 mb-1">Priority</label>
                    {editMode ? (
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
                    ) : (
                      <div className="flex items-center gap-2">
                        <Flag size={16} className={currentPriority?.color} />
                        <span className="text-slate-800">{currentPriority?.label}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-1">Due Date</label>
                  {editMode ? (
                    <input
                      type="datetime-local"
                      value={formData.due_date}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      className="input-field"
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-slate-800">
                      <Calendar size={16} className="text-slate-400" />
                      {task?.due_date
                        ? new Date(task.due_date).toLocaleString()
                        : 'No due date'}
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
                      {task?.contact_id
                        ? contactsList.find((c) => c.id === task.contact_id)?.name || '-'
                        : '-'}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">Quick Actions</h2>
              <div className="space-y-2">
                <button
                  onClick={() => handleStatusChange('pending')}
                  className={`w-full p-3 rounded-lg flex items-center gap-3 ${
                    task?.status === 'pending' ? 'bg-slate-100' : 'bg-slate-50'
                  }`}
                >
                  <div className="w-3 h-3 rounded-full bg-slate-500" />
                  <span className="text-slate-800">Pending</span>
                </button>
                <button
                  onClick={() => handleStatusChange('in_progress')}
                  className={`w-full p-3 rounded-lg flex items-center gap-3 ${
                    task?.status === 'in_progress' ? 'bg-blue-50' : 'bg-slate-50'
                  }`}
                >
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-slate-800">In Progress</span>
                </button>
                <button
                  onClick={() => handleStatusChange('completed')}
                  className={`w-full p-3 rounded-lg flex items-center gap-3 ${
                    task?.status === 'completed' ? 'bg-green-50' : 'bg-slate-50'
                  }`}
                >
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-slate-800">Completed</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}