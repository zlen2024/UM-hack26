'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { reports } from '@/lib/api';
import { BarChart3, TrendingUp, Users, DollarSign } from 'lucide-react';

export default function ReportsPage() {
  const router = useRouter();
  const [pipeline, setPipeline] = useState<any[]>([]);
  const [contactActivity, setContactActivity] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }
    loadReports();
  }, [router]);

  const loadReports = async () => {
    try {
      const [pipelineRes, contactsRes, metricsRes] = await Promise.all([
        reports.pipeline(),
        reports.contacts(),
        reports.dashboard(),
      ]);
      setPipeline(pipelineRes.data);
      setContactActivity(contactsRes.data);
      setMetrics(metricsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const stageColors: Record<string, string> = {
    lead: 'bg-blue-500',
    qualified: 'bg-cyan-500',
    proposal: 'bg-purple-500',
    won: 'bg-green-500',
    lost: 'bg-red-500',
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

  const totalValue = pipeline.reduce((sum, s) => sum + parseFloat(s.total_value || 0), 0);
  const wonValue = pipeline.find((s) => s.stage === 'won')?.total_value || 0;
  const winRate = metrics?.total_opportunities ? (wonValue / totalValue * 100).toFixed(1) : 0;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Reports</h1>
          <p className="text-slate-500">Analytics and insights</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-blue-500">
                <DollarSign className="text-white" size={24} />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Pipeline Value</p>
                <p className="text-2xl font-bold text-slate-800">
                  ${totalValue.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-green-500">
                <TrendingUp className="text-white" size={24} />
              </div>
              <div>
                <p className="text-sm text-slate-500">Won Value</p>
                <p className="text-2xl font-bold text-slate-800">
                  ${wonValue.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-purple-500">
                <BarChart3 className="text-white" size={24} />
              </div>
              <div>
                <p className="text-sm text-slate-500">Win Rate</p>
                <p className="text-2xl font-bold text-slate-800">{winRate}%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="card">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Pipeline by Stage</h2>
            <div className="space-y-4">
              {pipeline.map((stage) => (
                <div key={stage.stage}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600 capitalize">{stage.stage}</span>
                    <span className="font-medium text-slate-800">
                      ${parseFloat(stage.total_value || 0).toLocaleString()} ({stage.count})
                    </span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${stageColors[stage.stage] || 'bg-slate-500'} rounded-full`}
                      style={{
                        width: `${totalValue ? (stage.total_value / totalValue) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">Contact Activity</h2>
            {contactActivity.length === 0 ? (
              <div className="text-slate-500 text-center py-4">No activity yet</div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {contactActivity.slice(0, 10).map((contact) => (
                  <div key={contact.contact_id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                        <Users size={16} className="text-primary" />
                      </div>
                      <span className="font-medium text-slate-800">{contact.contact_name}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm text-slate-600">{contact.activity_count} activities</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}