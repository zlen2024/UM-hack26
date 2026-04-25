'use client';
import { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d';

interface Node {
  id: string;
  label: string;
  properties: any;
  val?: number;
}

interface Link {
  source: string;
  target: string;
  relationship_type: string;
  properties: any;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

export default function KnowledgeGraph({ 
  data, 
  onNodeClick 
}: { 
  data: GraphData, 
  onNodeClick: (node: Node) => void 
}) {
  const fgRef = useRef<ForceGraphMethods>();
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  
  // Update graph data when props change, but keep the layout
  useEffect(() => {
    // ForceGraph expects 'source' and 'target' which we map from 'from' and 'to' in the API
    const formattedData = {
      nodes: data.nodes.map(n => ({ ...n, val: 5 })),
      links: data.links.map((l: any) => ({
        ...l,
        source: l.from || l.source,
        target: l.to || l.target,
      }))
    };
    setGraphData(formattedData);
  }, [data]);

  return (
    <div className="w-full h-full bg-white border border-slate-200 rounded-lg overflow-hidden relative">
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel="id"
        nodeAutoColorBy="label"
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        linkWidth={1.5}
        linkLabel="relationship_type"
        onNodeClick={onNodeClick}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.id;
          const fontSize = 12/globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          const textWidth = ctx.measureText(label).width;
          const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = node.color || '#2563eb';
          ctx.fillText(label, node.x, node.y);

          node.__bckgDimensions = bckgDimensions;
        }}
        nodePointerAreaPaint={(node: any, color, ctx) => {
          ctx.fillStyle = color;
          const bckgDimensions = node.__bckgDimensions;
          bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);
        }}
      />
    </div>
  );
}