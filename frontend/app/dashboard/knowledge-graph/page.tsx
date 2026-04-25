'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { cs } from '@/lib/api';
import KnowledgeGraphClient from '@/components/KnowledgeGraphClient';

export default function KnowledgeGraphPage() {
  const router = useRouter();
  const [data, setData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [editLabel, setEditLabel] = useState('');
  const [editProps, setEditProps] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadGraph();
  }, [router]);

  const loadGraph = async () => {
    try {
      const res = await cs.getGraph();
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (node: any) => {
    setSelectedNode(node);
    setEditLabel(node.label || '');
    setEditProps(JSON.stringify(node.properties || {}, null, 2));
  };

  const handleSaveNode = async () => {
    if (!selectedNode) return;
    setSaving(true);
    try {
      let parsedProps = {};
      try {
        parsedProps = JSON.parse(editProps);
      } catch(e) {
        alert("Invalid JSON in properties");
        setSaving(false);
        return;
      }
      
      await cs.editNode(selectedNode.id, editLabel, parsedProps);
      setSelectedNode(null);
      await loadGraph();
    } catch (err) {
      console.error(err);
      alert("Failed to save node");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <div className="text-slate-500">Loading Knowledge Graph...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col p-8 h-full">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Knowledge Graph</h1>
            <p className="text-slate-500">Manage and view agent knowledge entities and relationships.</p>
          </div>
          <button 
            onClick={loadGraph}
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        <div className="flex-1 relative bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {/* We pass edges as links for the graph component */}
          <KnowledgeGraphClient data={{ nodes: data.nodes, links: data.edges }} onNodeClick={handleNodeClick} />
        </div>
      </main>

      {/* Edit Node Modal */}
      {selectedNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
              <h3 className="font-semibold text-slate-800">Edit Node: {selectedNode.id}</h3>
              <button 
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                &times;
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Label
                </label>
                <input
                  type="text"
                  value={editLabel}
                  onChange={(e) => setEditLabel(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Properties (JSON)
                </label>
                <textarea
                  value={editProps}
                  onChange={(e) => setEditProps(e.target.value)}
                  className="w-full h-32 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>
            </div>
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
              <button
                onClick={() => setSelectedNode(null)}
                className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNode}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}