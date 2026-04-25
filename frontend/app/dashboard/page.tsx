'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { reports, tasks as tasksApi, opportunities as opportunitiesApi, businessBackground as businessApi } from '@/lib/api';
import { getCache, setCache, preloadUserData, getPreloadedData } from '@/lib/cache';
import { Users, CheckSquare, DollarSign, TrendingUp, Clock, Sparkles, Target, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [pipeline, setPipeline] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [hasBusinessBackground, setHasBusinessBackground] = useState<boolean>(true);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/');
      return;
    }

    const cachedData = getPreloadedData();
    if (cachedData.metrics && cachedData.pipeline && cachedData.tasks && cachedData.opportunities) {
      console.log('[Dashboard] Using cached data');
      setMetrics(cachedData.metrics);
      setPipeline(cachedData.pipeline);
      setTasks(cachedData.tasks);
      setOpportunities(cachedData.opportunities);
      setLoading(false);
      
      preloadUserData().then(() => {
        console.log('[Dashboard] Background refresh complete');
        loadDashboard();
      });
    } else {
      loadDashboard();
    }
  }, [router]);

  const loadDashboard = async () => {
    try {
      setIsRefreshing(true);
      const [metricsRes, pipelineRes, tasksRes, oppsRes, bgRes] = await Promise.all([
        reports.dashboard(),
        reports.pipeline(),
        tasksApi.list(),
        opportunitiesApi.list(),
        businessApi.list()
      ]);
      
      setMetrics(metricsRes.data);
      setPipeline(pipelineRes.data);
      setTasks(tasksRes.data);
      setOpportunities(oppsRes.data);
      setHasBusinessBackground(bgRes.data && bgRes.data.length > 0);
      
      setCache('metrics', metricsRes.data);
      setCache('pipeline', pipelineRes.data);
      setCache('tasks', tasksRes.data);
      setCache('opportunities', oppsRes.data);
      
      console.log('[Dashboard] Data loaded and cached');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const statCards = [
    {
      label: 'Total Contacts',
      value: metrics?.total_contacts || 0,
      icon: Users,
      tone: 'from-blue-600 to-indigo-700',
      detail: 'People in your CRM',
    },
    {
      label: 'Pipeline Value',
      value: `$${(metrics?.pipeline_value || 0).toLocaleString()}`,
      icon: DollarSign,
      tone: 'from-sky-500 to-blue-600',
      detail: 'Active revenue in flight',
    },
    {
      label: 'Won Value',
      value: `$${(metrics?.won_value || 0).toLocaleString()}`,
      icon: TrendingUp,
      tone: 'from-indigo-600 to-blue-700',
      detail: 'Closed this cycle',
    },
    {
      label: 'Open Tasks',
      value: metrics?.open_tasks || 0,
      icon: CheckSquare,
      tone: 'from-slate-600 to-blue-600',
      detail: 'Still in motion',
    },
  ];

  const stagePalette: Record<string, string> = {
    lead: '#38bdf8',
    qualified: '#6366f1',
    proposal: '#f59e0b',
    won: '#2563eb',
    lost: '#ef4444',
  };

  const pipelineTotal = pipeline.reduce(
    (sum, stage) => sum + Number(stage.total_value || 0),
    0
  );

  const donutGradient = useMemo(() => {
    if (!pipelineTotal) return 'conic-gradient(#e2e8f0 0deg 360deg)';
    let current = 0;
    const segments = pipeline.map((stage) => {
      const value = Number(stage.total_value || 0);
      const angle = (value / pipelineTotal) * 360;
      const color = stagePalette[stage.stage] || '#94a3b8';
      const start = current;
      const end = current + angle;
      current = end;
      return `${color} ${start}deg ${end}deg`;
    });
    return `conic-gradient(${segments.join(', ')})`;
  }, [pipeline, pipelineTotal]);

  const nextTasks = useMemo(() => {
    return [...tasks]
      .filter((task) => task.status !== 'completed')
      .sort((a, b) => {
        const aTime = a.due_date ? new Date(a.due_date).getTime() : Number.MAX_SAFE_INTEGER;
        const bTime = b.due_date ? new Date(b.due_date).getTime() : Number.MAX_SAFE_INTEGER;
        return aTime - bTime;
      })
      .slice(0, 5);
  }, [tasks]);

  const topOpportunities = useMemo(() => {
    return [...opportunities]
      .sort((a, b) => Number(b.value || 0) - Number(a.value || 0))
      .slice(0, 5);
  }, [opportunities]);

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
        <div className="mb-10 animate-fade-up">
          <div className="flex items-center gap-3 page-kicker">
            <Sparkles size={16} className="text-blue-600" />
            Momentum snapshot
          </div>
          <h1 className="page-title mt-3">Dashboard</h1>
          <p className="text-muted mt-2">
            Track your shared pipeline, priorities, and next actions.
          </p>
        </div>

        {!hasBusinessBackground && (
          <div className="mb-8 rounded-2xl bg-amber-50 border border-amber-200 p-4 flex items-start gap-3 animate-fade-up">
            <AlertTriangle className="text-amber-500 mt-0.5 shrink-0" size={20} />
            <div>
              <h3 className="font-semibold text-amber-800">Setup your Business Context</h3>
              <p className="text-amber-700 text-sm mt-1">
                Your AI agent works best when it knows about your business. Add some company background, products, or FAQs.
              </p>
              <Link href="/business" className="inline-block mt-3 text-sm font-semibold text-amber-800 hover:text-amber-900 underline underline-offset-2">
                Add Business Background →
              </Link>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          {statCards.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div
                key={i}
                className="card card-elevated animate-fade-up"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-2xl bg-gradient-to-br ${stat.tone} text-white shadow-soft`}>
                    <Icon className="text-white" size={22} />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-muted">{stat.label}</p>
                    <p className="text-2xl font-semibold text-ink mt-1">{stat.value}</p>
                    <p className="text-xs text-muted mt-1">{stat.detail}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-10">
          <div className="card card-elevated xl:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="page-kicker">Revenue lens</div>
                <h2 className="text-xl font-semibold text-ink">Pipeline Mix</h2>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted">
                <Target size={16} />
                ${pipelineTotal.toLocaleString()}
              </div>
            </div>
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex items-center justify-center">
                <div
                  className="w-40 h-40 rounded-full relative"
                  style={{ background: donutGradient }}
                >
                  <div className="absolute inset-4 bg-white rounded-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-xl font-semibold text-ink">
                        {metrics?.total_opportunities || 0}
                      </div>
                      <div className="text-xs text-muted">Opportunities</div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-1 space-y-3">
                {pipeline.map((stage) => (
                  <div key={stage.stage} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: stagePalette[stage.stage] || '#94a3b8' }}
                      />
                      <span className="capitalize text-ink">{stage.stage}</span>
                    </div>
                    <div className="text-sm text-muted">
                      ${Number(stage.total_value || 0).toLocaleString()} ({stage.count})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card card-elevated">
            <div className="page-kicker">Priority queue</div>
            <h2 className="text-xl font-semibold text-ink mb-4">Next Actions</h2>
            {nextTasks.length === 0 ? (
              <div className="text-muted text-sm">No open tasks yet.</div>
            ) : (
              <div className="space-y-3">
                {nextTasks.map((task) => (
                  <div key={task.id} className="flex items-start justify-between rounded-2xl bg-wash px-3 py-2">
                    <div>
                      <div className="text-sm font-semibold text-ink">{task.title}</div>
                      <div className="text-xs text-muted">
                        {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}
                      </div>
                    </div>
                    <span className="text-xs text-muted uppercase tracking-[0.2em]">{task.priority}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="card card-elevated">
            <div className="page-kicker">High value</div>
            <h2 className="text-xl font-semibold text-ink mb-4">Top Opportunities</h2>
            {topOpportunities.length === 0 ? (
              <div className="text-muted text-sm">No opportunities yet.</div>
            ) : (
              <div className="space-y-3">
                {topOpportunities.map((opp) => (
                  <div key={opp.id} className="flex items-center justify-between rounded-2xl bg-wash px-3 py-2">
                    <div>
                      <div className="text-sm font-semibold text-ink">{opp.title}</div>
                      <div className="text-xs text-muted uppercase tracking-[0.2em]">{opp.stage}</div>
                    </div>
                    <div className="text-sm font-semibold text-blue-700">
                      ${Number(opp.value || 0).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="card card-elevated">
            <div className="page-kicker">Operating tempo</div>
            <h2 className="text-xl font-semibold text-ink mb-4">Workload Pulse</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm rounded-2xl bg-wash px-3 py-2">
                <div className="flex items-center gap-2 text-muted">
                  <Clock size={16} />
                  Open tasks
                </div>
                <span className="font-semibold text-ink">{metrics?.open_tasks || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm rounded-2xl bg-wash px-3 py-2">
                <div className="flex items-center gap-2 text-muted">
                  <Users size={16} />
                  Contacts
                </div>
                <span className="font-semibold text-ink">{metrics?.total_contacts || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm rounded-2xl bg-wash px-3 py-2">
                <div className="flex items-center gap-2 text-muted">
                  <TrendingUp size={16} />
                  Opportunities
                </div>
                <span className="font-semibold text-ink">{metrics?.total_opportunities || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}