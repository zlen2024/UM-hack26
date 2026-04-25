'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { kg } from '@/lib/api';
import { Plus, Edit, Trash2, Network, Link as LinkIcon, X } from 'lucide-react';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

type NodeData = { id: string; label: string; properties: string; val?: number; x?: number; y?: number };
type LinkData = { source: string | NodeData; target: string | NodeData; type: string; properties: string };

export default function KnowledgeGraphPage() {
  const router = useRouter();
  const [graphData, setGraphData] = useState<{ nodes: NodeData[]; links: LinkData[] }>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Selection state
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [selectedLink, setSelectedLink] = useState<LinkData | null>(null);
  
  // Modal state
  const [showNodeModal, setShowNodeModal] = useState(false);
  const [nodeModalMode, setNodeModalMode] = useState<'create' | 'edit'>('create');
  const [nodeForm, setNodeForm] = useState({ id: '', label: '', properties: '' });

  const [showEdgeModal, setShowEdgeModal] = useState(false);
  const [edgeModalMode, setEdgeModalMode] = useState<'create' | 'edit'>('create');
  const [edgeForm, setEdgeForm] = useState({ source: '', target: '', type: '', properties: '' });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadGraph();
  }, [router]);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    window.addEventListener('resize', updateDimensions);
    updateDimensions();
    // small delay to ensure layout is complete
    setTimeout(updateDimensions, 100);
    
    return () => window.removeEventListener('resize', updateDimensions);
  }, [loading]);

  const loadGraph = async () => {
    try {
      const res = await kg.getGraph();
      const data = res.data;
      setGraphData({
        nodes: data.nodes || [],
        links: (data.edges || []).map((e: any) => ({ ...e }))
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = useCallback((node: NodeData) => {
    setSelectedNode(node);
    setSelectedLink(null);
  }, []);

  const handleLinkClick = useCallback((link: LinkData) => {
    setSelectedLink(link);
    setSelectedNode(null);
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedLink(null);
  }, []);

  // Node Actions
  const openCreateNodeModal = () => {
    setNodeModalMode('create');
    setNodeForm({ id: '', label: '', properties: '' });
    setShowNodeModal(true);
  };

  const openEditNodeModal = () => {
    if (!selectedNode) return;
    setNodeModalMode('edit');
    setNodeForm({ 
      id: selectedNode.id, 
      label: selectedNode.label || '', 
      properties: selectedNode.properties || '' 
    });
    setShowNodeModal(true);
  };

  const handleDeleteNode = async () => {
    if (!selectedNode || !confirm('Are you sure you want to delete this node?')) return;
    try {
      await kg.deleteNode(selectedNode.id);
      setSelectedNode(null);
      loadGraph();
    } catch (err) {
      console.error(err);
      alert('Error deleting node');
    }
  };

  const handleNodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (nodeModalMode === 'create') {
        await kg.addNode(nodeForm);
      } else {
        await kg.updateNode(nodeForm);
      }
      setShowNodeModal(false);
      loadGraph();
    } catch (err) {
      console.error(err);
      alert('Error saving node');
    }
  };

  // Edge Actions
  const openCreateEdgeModal = () => {
    setEdgeModalMode('create');
    setEdgeForm({ 
      source: selectedNode ? selectedNode.id : '', 
      target: '', 
      type: '', 
      properties: '' 
    });
    setShowEdgeModal(true);
  };

  const openEditEdgeModal = () => {
    if (!selectedLink) return;
    const sourceId = typeof selectedLink.source === 'object' ? selectedLink.source.id : selectedLink.source;
    const targetId = typeof selectedLink.target === 'object' ? selectedLink.target.id : selectedLink.target;
    
    setEdgeModalMode('edit');
    setEdgeForm({ 
      source: sourceId, 
      target: targetId, 
      type: selectedLink.type || '', 
      properties: selectedLink.properties || '' 
    });
    setShowEdgeModal(true);
  };

  const handleDeleteEdge = async () => {
    if (!selectedLink || !confirm('Are you sure you want to delete this edge?')) return;
    const sourceId = typeof selectedLink.source === 'object' ? selectedLink.source.id : selectedLink.source;
    const targetId = typeof selectedLink.target === 'object' ? selectedLink.target.id : selectedLink.target;
    
    try {
      await kg.deleteEdge(sourceId, targetId, selectedLink.type);
      setSelectedLink(null);
      loadGraph();
    } catch (err) {
      console.error(err);
      alert('Error deleting edge');
    }
  };

  const handleEdgeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (edgeModalMode === 'create') {
        await kg.addEdge(edgeForm);
      } else {
        await kg.updateEdge(edgeForm);
      }
      setShowEdgeModal(false);
      loadGraph();
    } catch (err) {
      console.error(err);
      alert('Error saving edge');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-muted">Loading Graph...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      <Sidebar />
      <div className="flex-1 p-6 lg:p-10 flex flex-col h-screen overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-6 shrink-0">
          <div>
            <div className="page-kicker">Data Explorer</div>
            <h1 className="page-title mt-2">Knowledge Graph</h1>
            <p className="text-muted mt-2">Visualize and manage your entities and relationships.</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={openCreateNodeModal} className="btn-secondary flex items-center gap-2">
              <Plus size={18} />
              Add Node
            </button>
            <button onClick={openCreateEdgeModal} className="btn-secondary flex items-center gap-2">
              <LinkIcon size={18} />
              Add Edge
            </button>
          </div>
        </div>

        <div className="flex-1 flex gap-6 overflow-hidden">
          {/* Graph Container */}
          <div 
            className="flex-1 card p-0 overflow-hidden relative bg-slate-50" 
            ref={containerRef}
          >
            <ForceGraph2D
              width={dimensions.width}
              height={dimensions.height}
              graphData={graphData}
              nodeLabel="label"
              nodeColor={(node: any) => selectedNode?.id === node.id ? '#4f46e5' : '#3b82f6'}
              nodeRelSize={6}
              linkColor={(link: any) => selectedLink === link ? '#ef4444' : '#94a3b8'}
              linkWidth={(link: any) => selectedLink === link ? 3 : 1}
              linkLabel="type"
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              onNodeClick={handleNodeClick as any}
              onLinkClick={handleLinkClick as any}
              onBackgroundClick={handleBackgroundClick}
              // To enable text on links we would need to draw on canvas but let's keep it simple with default ForceGraph behavior.
            />
            
            {/* Quick stats overlay */}
            <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur px-3 py-2 rounded-lg text-xs font-semibold text-muted shadow-sm border border-slate-200">
              {graphData.nodes.length} Nodes • {graphData.links.length} Edges
            </div>
          </div>

          {/* Inspector Panel */}
          <div className="w-80 shrink-0 flex flex-col gap-4 overflow-y-auto">
            {selectedNode ? (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-ink flex items-center gap-2">
                    <Network size={16} className="text-blue-600" />
                    Node Details
                  </h3>
                  <button onClick={() => setSelectedNode(null)} className="text-muted hover:text-ink">
                    <X size={16} />
                  </button>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">ID</div>
                    <div className="font-medium text-sm break-all">{selectedNode.id}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">Label</div>
                    <div className="font-medium text-sm">{selectedNode.label || '-'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">Properties</div>
                    <div className="text-sm bg-slate-50 p-2 rounded border border-slate-100 whitespace-pre-wrap font-mono text-xs">
                      {selectedNode.properties || '-'}
                    </div>
                  </div>
                </div>
                <div className="mt-6 flex gap-2">
                  <button onClick={openEditNodeModal} className="flex-1 btn-secondary text-sm py-1.5 flex justify-center gap-1">
                    <Edit size={14} /> Edit
                  </button>
                  <button onClick={handleDeleteNode} className="flex-1 btn-secondary text-sm py-1.5 text-rose-600 hover:bg-rose-50 flex justify-center gap-1">
                    <Trash2 size={14} /> Delete
                  </button>
                </div>
                <div className="mt-2">
                  <button onClick={openCreateEdgeModal} className="w-full btn-primary text-sm py-1.5 flex justify-center gap-1">
                    <LinkIcon size={14} /> Connect
                  </button>
                </div>
              </div>
            ) : selectedLink ? (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-ink flex items-center gap-2">
                    <LinkIcon size={16} className="text-indigo-600" />
                    Edge Details
                  </h3>
                  <button onClick={() => setSelectedLink(null)} className="text-muted hover:text-ink">
                    <X size={16} />
                  </button>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">Source</div>
                    <div className="font-medium text-sm break-all">
                      {typeof selectedLink.source === 'object' ? selectedLink.source.id : selectedLink.source}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">Target</div>
                    <div className="font-medium text-sm break-all">
                      {typeof selectedLink.target === 'object' ? selectedLink.target.id : selectedLink.target}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">Type</div>
                    <div className="font-medium text-sm">{selectedLink.type || '-'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted uppercase tracking-wider">Properties</div>
                    <div className="text-sm bg-slate-50 p-2 rounded border border-slate-100 whitespace-pre-wrap font-mono text-xs">
                      {selectedLink.properties || '-'}
                    </div>
                  </div>
                </div>
                <div className="mt-6 flex gap-2">
                  <button onClick={openEditEdgeModal} className="flex-1 btn-secondary text-sm py-1.5 flex justify-center gap-1">
                    <Edit size={14} /> Edit
                  </button>
                  <button onClick={handleDeleteEdge} className="flex-1 btn-secondary text-sm py-1.5 text-rose-600 hover:bg-rose-50 flex justify-center gap-1">
                    <Trash2 size={14} /> Delete
                  </button>
                </div>
              </div>
            ) : (
              <div className="card flex flex-col items-center justify-center text-center py-12 px-4 border-dashed border-2 border-slate-200">
                <Network size={32} className="text-slate-300 mb-3" />
                <h3 className="font-semibold text-ink mb-1">No Selection</h3>
                <p className="text-sm text-muted">Click on a node or edge to view its details and manage it.</p>
              </div>
            )}
          </div>
        </div>

        {/* Node Modal */}
        {showNodeModal && (
          <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50">
            <div className="modal-panel p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-ink mb-4">
                {nodeModalMode === 'create' ? 'Add Node' : 'Edit Node'}
              </h2>
              <form onSubmit={handleNodeSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">ID (Unique) *</label>
                  <input
                    type="text"
                    value={nodeForm.id}
                    onChange={(e) => setNodeForm({ ...nodeForm, id: e.target.value })}
                    className="input-field"
                    required
                    disabled={nodeModalMode === 'edit'}
                  />
                  {nodeModalMode === 'edit' && <p className="text-xs text-muted mt-1">ID cannot be changed</p>}
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Label</label>
                  <input
                    type="text"
                    value={nodeForm.label}
                    onChange={(e) => setNodeForm({ ...nodeForm, label: e.target.value })}
                    className="input-field"
                    placeholder="e.g. Person, Company"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Properties (JSON string)</label>
                  <textarea
                    value={nodeForm.properties}
                    onChange={(e) => setNodeForm({ ...nodeForm, properties: e.target.value })}
                    className="input-field font-mono text-sm"
                    rows={4}
                    placeholder='{"name": "John", "age": 30}'
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowNodeModal(false)} className="flex-1 btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" className="flex-1 btn-primary">
                    {nodeModalMode === 'create' ? 'Save Node' : 'Update Node'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edge Modal */}
        {showEdgeModal && (
          <div className="fixed inset-0 modal-overlay flex items-center justify-center z-50">
            <div className="modal-panel p-6 w-full max-w-md">
              <h2 className="text-xl font-semibold text-ink mb-4">
                {edgeModalMode === 'create' ? 'Add Edge' : 'Edit Edge'}
              </h2>
              <form onSubmit={handleEdgeSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Source Node ID *</label>
                  <input
                    type="text"
                    value={edgeForm.source}
                    onChange={(e) => setEdgeForm({ ...edgeForm, source: e.target.value })}
                    className="input-field"
                    required
                    disabled={edgeModalMode === 'edit'}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Target Node ID *</label>
                  <input
                    type="text"
                    value={edgeForm.target}
                    onChange={(e) => setEdgeForm({ ...edgeForm, target: e.target.value })}
                    className="input-field"
                    required
                    disabled={edgeModalMode === 'edit'}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Relationship Type *</label>
                  <input
                    type="text"
                    value={edgeForm.type}
                    onChange={(e) => setEdgeForm({ ...edgeForm, type: e.target.value })}
                    className="input-field"
                    required
                    disabled={edgeModalMode === 'edit'}
                    placeholder="e.g. WORKS_AT, KNOWS"
                  />
                  {edgeModalMode === 'edit' && <p className="text-xs text-muted mt-1">Source, Target and Type identify the edge and cannot be changed</p>}
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ink mb-1">Properties (JSON string)</label>
                  <textarea
                    value={edgeForm.properties}
                    onChange={(e) => setEdgeForm({ ...edgeForm, properties: e.target.value })}
                    className="input-field font-mono text-sm"
                    rows={4}
                    placeholder='{"since": "2020", "role": "developer"}'
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowEdgeModal(false)} className="flex-1 btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" className="flex-1 btn-primary">
                    {edgeModalMode === 'create' ? 'Save Edge' : 'Update Edge'}
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
