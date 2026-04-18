'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import DataTable, { TableColumn } from 'react-data-table-component';
import Sidebar from '@/components/Sidebar';
import { reports } from '@/lib/api';
import { dataTablePaginationOptions, dataTableStyles } from '@/lib/tableStyles';
import { BarChart3, TrendingUp, Users, DollarSign, Activity, Target } from 'lucide-react';

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
    qualified: 'bg-indigo-500',
    proposal: 'bg-amber-500',
    won: 'bg-blue-700',
    lost: 'bg-rose-500',
  };

  const totalValue = pipeline.reduce((sum, s) => sum + parseFloat(s.total_value || 0), 0);
  const wonValue = pipeline.find((s) => s.stage === 'won')?.total_value || 0;
  const winRate = metrics?.total_opportunities ? (wonValue / totalValue * 100).toFixed(1) : 0;

  const pipelineColumns = useMemo<TableColumn<any>[]>(
    () => [
      {
        name: 'Stage',
        selector: (row) => row.stage,
        sortable: true,
        cell: (row) => (
          <span className="capitalize text-ink">{row.stage}</span>
        ),
      },
      {
        name: 'Count',
        selector: (row) => row.count,
        sortable: true,
        cell: (row) => <span className="text-muted">{row.count}</span>,
        width: '120px',
      },
      {
        name: 'Total Value',
        selector: (row) => row.total_value,
        sortable: true,
        cell: (row) => (
          <span className="text-ink">
            ${parseFloat(row.total_value || 0).toLocaleString()}
          </span>
        ),
      },
    ],
    []
  );

  const activityColumns = useMemo<TableColumn<any>[]>(
    () => [
      {
        name: 'Contact',
        selector: (row) => row.contact_name,
        sortable: true,
        cell: (row) => <span className="text-ink">{row.contact_name}</span>,
      },
      {
        name: 'Activities',
        selector: (row) => row.activity_count,
        sortable: true,
        cell: (row) => <span className="text-muted">{row.activity_count}</span>,
        width: '140px',
      },
      {
        name: 'Last Activity',
        selector: (row) => row.last_activity || '',
        sortable: true,
        cell: (row) => (
          <span className="text-muted">
            {row.last_activity ? new Date(row.last_activity).toLocaleDateString() : '-'}
          </span>
        ),
        width: '160px',
      },
    ],
    []
  );

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
        <div className="mb-10">
          <div className="flex items-center gap-3 page-kicker">
            <Activity size={16} className="text-blue-600" />
            Analytics and insights
          </div>
          <h1 className="page-title mt-3">Reports</h1>
          <p className="text-muted mt-2">Live revenue signals and activity trends.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="card card-elevated">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-soft">
                <DollarSign size={22} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Total Pipeline Value</p>
                <p className="text-2xl font-semibold text-ink mt-1">
                  ${totalValue.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="card card-elevated">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-soft">
                <TrendingUp size={22} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Won Value</p>
                <p className="text-2xl font-semibold text-ink mt-1">
                  ${wonValue.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="card card-elevated">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl bg-gradient-to-br from-sky-600 to-blue-600 text-white shadow-soft">
                <BarChart3 size={22} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Win Rate</p>
                <p className="text-2xl font-semibold text-ink mt-1">{winRate}%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          <div className="card card-elevated">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="page-kicker">Stage health</div>
                <h2 className="text-xl font-semibold text-ink">Pipeline by Stage</h2>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted">
                <Target size={16} />
                ${totalValue.toLocaleString()}
              </div>
            </div>
            <div className="space-y-4">
              {pipeline.map((stage) => (
                <div key={stage.stage}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted uppercase tracking-[0.2em]">{stage.stage}</span>
                    <span className="font-semibold text-ink">
                      ${parseFloat(stage.total_value || 0).toLocaleString()} ({stage.count})
                    </span>
                  </div>
                  <div className="h-2 bg-wash rounded-full overflow-hidden">
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

          <div className="card card-elevated">
            <div className="page-kicker">Engagement</div>
            <h2 className="text-xl font-semibold text-ink mb-4">Contact Activity</h2>
            {contactActivity.length === 0 ? (
              <div className="text-muted text-center py-4">No activity yet</div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {contactActivity.slice(0, 10).map((contact) => (
                  <div key={contact.contact_id} className="flex items-center justify-between rounded-2xl bg-wash px-3 py-2">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 bg-blue-50 rounded-full flex items-center justify-center">
                        <Users size={16} className="text-blue-700" />
                      </div>
                      <span className="font-semibold text-ink">{contact.contact_name}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm text-muted">{contact.activity_count} activities</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card card-elevated">
            <h2 className="text-xl font-semibold text-ink mb-4">Pipeline Table</h2>
            <DataTable
              columns={pipelineColumns}
              data={pipeline}
              pagination
              highlightOnHover
              customStyles={dataTableStyles}
              paginationComponentOptions={dataTablePaginationOptions}
            />
          </div>
          <div className="card card-elevated">
            <h2 className="text-xl font-semibold text-ink mb-4">Activity Table</h2>
            <DataTable
              columns={activityColumns}
              data={contactActivity}
              pagination
              highlightOnHover
              customStyles={dataTableStyles}
              paginationComponentOptions={dataTablePaginationOptions}
            />
          </div>
        </div>
      </div>
    </div>
  );
}