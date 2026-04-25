'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { businessBackground as businessApi } from '@/lib/api';
import { Plus, Search, Trash2, Edit2, Save, X, Eye, Calendar, User, ToggleRight, ToggleLeft } from 'lucide-react';

type BusinessRow = {
  id: number;
  category: string;
  title: string;
  content: string;
  is_active: boolean;
  priority: number;
  tags?: string;
  usage_count?: number;
  created_at?: string;
};

export default function BusinessBackgroundPage() {
  const router = useRouter();
  const [backgroundsList, setBackgroundsList] = useState<BusinessRow[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  
  const [activeBgId, setActiveBgId] = useState<number | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({ 
    category: 'technology', 
    title: '', 
    content: '', 
    is_active: true, 
    priority: 1,
    tags: [] as string[]
  });
  const [tagInput, setTagInput] = useState('');

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
      if (res.data.length > 0 && activeBgId === null && !isEditing) {
        selectBackground(res.data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectBackground = (bg: BusinessRow) => {
    setActiveBgId(bg.id);
    setIsEditing(false);
    let parsedTags = [];
    try {
      parsedTags = bg.tags ? JSON.parse(bg.tags) : [];
    } catch(e) {}
    
    setFormData({
      category: bg.category || 'technology',
      title: bg.title || '',
      content: bg.content || '',
      is_active: bg.is_active,
      priority: bg.priority || 1,
      tags: parsedTags
    });
  };

  const handleAddNew = () => {
    setActiveBgId(null);
    setIsEditing(true);
    setFormData({ 
      category: 'technology', 
      title: '', 
      content: '', 
      is_active: true, 
      priority: 1,
      tags: []
    });
  };

  const handleSave = async () => {
    try {
      const payload = {
        ...formData,
        tags: formData.tags
      };
      
      if (activeBgId === null) {
        const res = await businessApi.create(payload);
        setActiveBgId(res.data.id);
      } else {
        await businessApi.update(activeBgId, payload);
      }
      setIsEditing(false);
      loadBackgrounds();
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancel = () => {
    if (activeBgId === null && backgroundsList.length > 0) {
      selectBackground(backgroundsList[0]);
    } else if (activeBgId !== null) {
      const current = backgroundsList.find(b => b.id === activeBgId);
      if (current) selectBackground(current);
    } else {
      setIsEditing(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this?')) return;
    try {
      await businessApi.delete(id);
      if (activeBgId === id) {
        setActiveBgId(null);
      }
      loadBackgrounds();
    } catch (err) {
      console.error(err);
    }
  };

  const addTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!formData.tags.includes(tagInput.trim())) {
        setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      }
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const getActiveRecord = () => {
    return backgroundsList.find(b => b.id === activeBgId);
  };

  const activeRecord = getActiveRecord();

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
    <div className="flex flex-col md:flex-row min-h-screen bg-[#F8FAFC]">
      <Sidebar />
      <div className="flex-1">
        {/* Top Header Bar */}
        <div className="h-16 border-b border-gray-200 bg-white flex items-center px-6 gap-4">
          <div className="relative w-full max-w-xl flex items-center bg-[#F1F5F9] rounded-lg px-3 py-2">
            <Search className="text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search businesses..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent border-none outline-none w-full ml-2 text-sm text-gray-700 placeholder-gray-400"
            />
          </div>
          <div className="flex-1 font-semibold text-center text-ink">Business Background</div>
          <div className="flex items-center gap-4 text-gray-500">
            {/* Placeholder icons */}
            <div className="w-5 h-5 rounded-full bg-gray-200"></div>
            <div className="w-5 h-5 rounded-full bg-gray-200"></div>
            <div className="w-8 h-8 rounded-full bg-blue-600 border-2 border-white shadow-sm"></div>
          </div>
        </div>

        <div className="p-6 lg:p-8 flex flex-col xl:flex-row gap-6">
          {/* Main Content Area */}
          <div className="flex-1 max-w-4xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Business Detail Form</h1>
                <p className="text-gray-500 text-sm mt-1">Manage and update background information for this entity.</p>
              </div>
              
              {isEditing ? (
                <div className="flex gap-3">
                  <button onClick={handleCancel} className="px-4 py-2 rounded-lg border border-gray-200 bg-white text-gray-700 text-sm font-semibold hover:bg-gray-50 transition-colors">
                    Cancel
                  </button>
                  <button onClick={handleSave} className="px-4 py-2 rounded-lg bg-[#0F62FE] text-white text-sm font-semibold flex items-center gap-2 hover:bg-blue-700 transition-colors">
                    <Save size={16} />
                    Save Changes
                  </button>
                </div>
              ) : (
                <div className="flex gap-3">
                  <button onClick={handleAddNew} className="px-4 py-2 rounded-lg border border-gray-200 bg-white text-gray-700 text-sm font-semibold hover:bg-gray-50 transition-colors flex items-center gap-2">
                    <Plus size={16} />
                    Add New
                  </button>
                  <button onClick={() => setIsEditing(true)} className="px-4 py-2 rounded-lg bg-[#0F62FE] text-white text-sm font-semibold flex items-center gap-2 hover:bg-blue-700 transition-colors" disabled={activeBgId === null}>
                    <Edit2 size={16} />
                    Edit Form
                  </button>
                </div>
              )}
            </div>

            <div className="space-y-6">
              {/* Identification Section */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Identification</h2>
                  <Edit2 size={16} className="text-gray-400" />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-semibold tracking-wider text-gray-500 uppercase mb-2">Category</label>
                    {isEditing ? (
                      <select
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                      >
                        <option value="technology">Technology</option>
                        <option value="finance">Finance</option>
                        <option value="healthcare">Healthcare</option>
                        <option value="retail">Retail</option>
                        <option value="other">Other</option>
                      </select>
                    ) : (
                      <div className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-gray-800 text-sm bg-gray-50 capitalize">
                        {formData.category || '-'}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs font-semibold tracking-wider text-gray-500 uppercase mb-2">Official Title</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g. Acme Corp International"
                      />
                    ) : (
                      <div className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-gray-800 text-sm bg-gray-50">
                        {formData.title || '-'}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Detailed Background Section */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Detailed Background</h2>
                  <Edit2 size={16} className="text-gray-400" />
                </div>
                
                <div>
                  <label className="block text-xs font-semibold tracking-wider text-gray-500 uppercase mb-2">Content Narrative</label>
                  {isEditing ? (
                    <textarea
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                      className="w-full border border-gray-200 rounded-lg px-4 py-3 text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[200px]"
                      placeholder="Enter the detailed background here..."
                    />
                  ) : (
                    <div className="w-full border border-gray-200 rounded-lg px-4 py-3 text-gray-800 text-sm bg-gray-50 min-h-[200px] whitespace-pre-wrap">
                      {formData.content || '-'}
                    </div>
                  )}
                  <div className="flex justify-between mt-2">
                    <span className="text-xs text-gray-400">Markdown supported</span>
                    <span className="text-xs text-gray-400">{formData.content.length} characters</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar Area */}
          <div className="w-full xl:w-80 flex flex-col gap-6">
            
            {/* Configuration Section */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Configuration</h2>
                <Edit2 size={16} className="text-gray-400" />
              </div>

              <div className="mb-6">
                <label className="block text-xs font-semibold tracking-wider text-gray-500 uppercase mb-3">Classification Tags</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.tags.map(tag => (
                    <span key={tag} className="inline-flex items-center gap-1 px-3 py-1 bg-[#EEF2FF] text-[#4F46E5] rounded-full text-xs font-semibold">
                      {tag}
                      {isEditing && (
                        <button onClick={() => removeTag(tag)} className="hover:text-blue-800 focus:outline-none">
                          <X size={12} />
                        </button>
                      )}
                    </span>
                  ))}
                  {isEditing && (
                    <input
                      type="text"
                      value={tagInput}
                      onChange={e => setTagInput(e.target.value)}
                      onKeyDown={addTag}
                      placeholder="+ Add Tag"
                      className="inline-flex items-center px-3 py-1 border border-dashed border-gray-300 rounded-full text-xs text-gray-600 focus:outline-none focus:border-blue-500 bg-transparent w-24"
                    />
                  )}
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-xs font-semibold tracking-wider text-gray-500 uppercase mb-3">Routing Priority</label>
                <div className="flex items-center gap-3">
                  {isEditing ? (
                    <input 
                      type="number" 
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 1 })}
                      className="w-16 border border-gray-200 rounded-lg px-3 py-2 text-center text-sm"
                      min="1"
                      max="10"
                    />
                  ) : (
                    <div className="w-16 border border-gray-200 rounded-lg px-3 py-2 text-center text-sm bg-gray-50">
                      {formData.priority}
                    </div>
                  )}
                  <span className="text-sm text-gray-600">Level {formData.priority} {formData.priority === 1 ? '(Highest)' : ''}</span>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-gray-900">Entity Status</div>
                  <div className="text-xs text-gray-500 mt-0.5">Currently {formData.is_active ? 'visible in production' : 'hidden'}</div>
                </div>
                <button 
                  onClick={() => isEditing && setFormData({...formData, is_active: !formData.is_active})}
                  disabled={!isEditing}
                  className={`focus:outline-none ${!isEditing ? 'cursor-default opacity-80' : ''}`}
                >
                  {formData.is_active ? (
                    <ToggleRight size={36} className="text-[#0F62FE]" />
                  ) : (
                    <ToggleLeft size={36} className="text-gray-300" />
                  )}
                </button>
              </div>
            </div>

            {/* Metrics & History Section */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Metrics & History</h2>
              
              <div className="bg-[#F8FAFC] border border-gray-100 rounded-xl p-4 flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#E0E7FF] flex items-center justify-center text-[#4F46E5]">
                    <Eye size={20} />
                  </div>
                  <span className="text-sm text-gray-600">Usage Count</span>
                </div>
                <span className="text-lg font-bold text-gray-900">
                  {(activeRecord?.usage_count || 0).toLocaleString()}
                </span>
              </div>

              <div className="space-y-4 text-sm">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 text-gray-500">
                    <Calendar size={14} />
                    <span>Created</span>
                  </div>
                  <span className="text-gray-900 font-medium">
                    {activeRecord?.created_at ? new Date(activeRecord.created_at).toLocaleDateString() : '-'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 text-gray-500">
                    <Calendar size={14} />
                    <span>Last Updated</span>
                  </div>
                  <span className="text-gray-900 font-medium">
                    {activeRecord?.created_at ? new Date(activeRecord.created_at).toLocaleDateString() : '-'}
                  </span>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <div className="flex items-center gap-2 text-gray-500">
                    <User size={14} />
                    <span>Modified By</span>
                  </div>
                  <span className="text-blue-600 font-medium truncate max-w-[120px]">
                    System User
                  </span>
                </div>
              </div>
            </div>
            
            {/* List Selection Sidebar (replaces the table) */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">Other Records</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                {backgroundsList.map(bg => (
                  <button 
                    key={bg.id}
                    onClick={() => selectBackground(bg)}
                    className={`w-full text-left p-3 rounded-lg border text-sm transition-colors ${activeBgId === bg.id ? 'border-blue-500 bg-blue-50' : 'border-gray-100 hover:border-gray-300'}`}
                  >
                    <div className="font-semibold text-gray-900 truncate">{bg.title || 'Untitled'}</div>
                    <div className="text-xs text-gray-500 mt-1 capitalize">{bg.category}</div>
                  </button>
                ))}
                {backgroundsList.length === 0 && (
                  <div className="text-sm text-gray-500 text-center py-4">No records found.</div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}