'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { reports, auth } from '@/lib/api';
import { Users, Building2, CheckSquare, DollarSign, TrendingUp, Clock } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadDashboard();
  }, [router]);

  const loadDashboard = async () => {
    try {
      const res = await reports.dashboard();
      setMetrics(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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

  const statCards = [
    {
      label: 'Total Contacts',
      value: metrics?.total_contacts || 0,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      label: 'Pipeline Value',
      value: `$${(metrics?.pipeline_value || 0).toLocaleString()}`,
      icon: DollarSign,
      color: 'bg-green-500',
    },
    {
      label: 'Won Value',
      value: `$${(metrics?.won_value || 0).toLocaleString()}`,
      icon: TrendingUp,
      color: 'bg-emerald-500',
    },
    {
      label: 'Open Tasks',
      value: metrics?.open_tasks || 0,
      icon: CheckSquare,
      color: 'bg-amber-500',
    },
  ];

  const pipelineStages = [
    { label: 'Leads', count: metrics?.leads_count || 0, color: 'bg-blue-500' },
    { label: 'Qualified', count: metrics?.qualified_count || 0, color: 'bg-cyan-500' },
    { label: 'Proposal', count: metrics?.proposal_count || 0, color: 'bg-purple-500' },
  ];

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-slate-500">Welcome back!</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div key={i} className="card">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${stat.color}`}>
                    <Icon className="text-white" size={24} />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">{stat.label}</p>
                    <p className="text-2xl font-bold text-slate-800">{stat.value}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Pipeline Overview</h2>
          <div className="space-y-4">
            {pipelineStages.map((stage, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600">{stage.label}</span>
                  <span className="font-medium text-slate-800">{stage.count}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${stage.color} rounded-full`}
                    style={{
                      width: `${metrics?.total_opportunities ? (stage.count / metrics.total_opportunities) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}