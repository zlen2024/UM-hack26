'use client';
import dynamic from 'next/dynamic';
import React, { Suspense } from 'react';

const KnowledgeGraphNoSSR = dynamic(() => import('./KnowledgeGraph'), { ssr: false });

export default function KnowledgeGraphClient(props: any) {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-full">Loading Graph...</div>}>
      <KnowledgeGraphNoSSR {...props} />
    </Suspense>
  );
}