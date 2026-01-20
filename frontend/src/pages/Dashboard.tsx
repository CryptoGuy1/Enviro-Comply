import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  Clock,
  TrendingUp,
  TrendingDown,
  FileWarning,
  Calendar,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { api } from '../lib/api';
import { cn } from '../lib/utils';
import ComplianceGauge from '../components/ComplianceGauge';
import GapCard from '../components/GapCard';

export default function Dashboard() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  const { data: facilities } = useQuery({
    queryKey: ['facilities'],
    queryFn: api.getFacilities,
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  const complianceScore = dashboard?.compliance_score ?? 85;
  const gapsSummary = dashboard?.gaps_summary ?? {
    critical: 1,
    high: 3,
    medium: 5,
    low: 8,
    total: 17,
  };

  // Mock trend data
  const trendData = [
    { month: 'Jul', score: 72 },
    { month: 'Aug', score: 75 },
    { month: 'Sep', score: 78 },
    { month: 'Oct', score: 82 },
    { month: 'Nov', score: 80 },
    { month: 'Dec', score: complianceScore },
  ];

  const gapDistribution = [
    { name: 'Critical', value: gapsSummary.critical, color: '#ef4444' },
    { name: 'High', value: gapsSummary.high, color: '#f97316' },
    { name: 'Medium', value: gapsSummary.medium, color: '#eab308' },
    { name: 'Low', value: gapsSummary.low, color: '#22c55e' },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Overview of environmental compliance status across all facilities
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Compliance Score"
          value={`${complianceScore}/100`}
          change={complianceScore >= 80 ? '+5%' : '-3%'}
          trend={complianceScore >= 80 ? 'up' : 'down'}
          icon={complianceScore >= 80 ? CheckCircle2 : AlertTriangle}
          iconColor={complianceScore >= 80 ? 'text-emerald-500' : 'text-amber-500'}
        />
        <StatCard
          title="Total Facilities"
          value={facilities?.length ?? 3}
          subtitle="Active monitoring"
          icon={Building2}
          iconColor="text-blue-500"
        />
        <StatCard
          title="Open Gaps"
          value={gapsSummary.total}
          change={`${gapsSummary.critical} critical`}
          trend={gapsSummary.critical > 0 ? 'down' : 'up'}
          icon={FileWarning}
          iconColor="text-red-500"
        />
        <StatCard
          title="Upcoming Deadlines"
          value="3"
          subtitle="Next 30 days"
          icon={Calendar}
          iconColor="text-purple-500"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance gauge */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Overall Compliance
          </h3>
          <div className="flex justify-center">
            <ComplianceGauge score={complianceScore} />
          </div>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              {complianceScore >= 90
                ? 'Excellent compliance posture'
                : complianceScore >= 75
                ? 'Good, minor improvements needed'
                : complianceScore >= 60
                ? 'Needs attention'
                : 'Critical action required'}
            </p>
          </div>
        </div>

        {/* Compliance trend */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Compliance Trend
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} />
                <YAxis domain={[0, 100]} stroke="#9ca3af" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="url(#colorScore)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Gap distribution and priority gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gap distribution pie chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Gap Distribution
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={gapDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {gapDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-3 mt-4">
            {gapDistribution.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-gray-600">
                  {item.name} ({item.value})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Priority gaps */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Priority Gaps</h3>
            <a
              href="/gaps"
              className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
            >
              View all →
            </a>
          </div>
          <div className="space-y-3">
            <GapCard
              title="LDAR Survey Overdue"
              facility="Permian Basin Facility 1"
              severity="critical"
              deadline="2025-01-15"
              regulation="40 CFR 60.5397a"
            />
            <GapCard
              title="High-Bleed Pneumatic Controllers"
              facility="Bakken Gathering Station"
              severity="high"
              deadline="2025-03-01"
              regulation="40 CFR 60.5390a"
            />
            <GapCard
              title="Permit Expiring Soon"
              facility="Wyoming Gas Processing Plant"
              severity="high"
              deadline="2025-03-15"
              regulation="Title V Permit"
            />
          </div>
        </div>
      </div>

      {/* Recent alerts */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Alerts</h3>
          <span className="text-xs text-gray-500">Last 7 days</span>
        </div>
        <div className="space-y-3">
          {(dashboard?.recent_alerts ?? []).length > 0 ? (
            dashboard.recent_alerts.map((alert: any, index: number) => (
              <AlertItem key={index} alert={alert} />
            ))
          ) : (
            <>
              <AlertItem
                alert={{
                  type: 'regulatory_update',
                  message: 'EPA finalized amendments to NSPS OOOOb - New methane requirements effective Q2 2025',
                  severity: 'info',
                }}
              />
              <AlertItem
                alert={{
                  type: 'deadline',
                  message: 'Annual GHG report (Subpart W) due in 45 days',
                  severity: 'warning',
                }}
              />
              <AlertItem
                alert={{
                  type: 'gap_identified',
                  message: 'New compliance gap identified at Permian Basin Facility 1',
                  severity: 'error',
                }}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Stat card component
function StatCard({
  title,
  value,
  change,
  subtitle,
  trend,
  icon: Icon,
  iconColor,
}: {
  title: string;
  value: string | number;
  change?: string;
  subtitle?: string;
  trend?: 'up' | 'down';
  icon: any;
  iconColor: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div className={cn('p-2 rounded-lg bg-gray-50', iconColor)}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <div
            className={cn(
              'flex items-center gap-1 text-xs font-medium',
              trend === 'up' ? 'text-emerald-600' : 'text-red-600'
            )}
          >
            {trend === 'up' ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {change}
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
        <p className="text-sm text-gray-500 mt-1">{subtitle || title}</p>
      </div>
    </div>
  );
}

// Alert item component
function AlertItem({ alert }: { alert: any }) {
  const severityStyles = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  };

  const severityIcons = {
    info: Clock,
    warning: AlertTriangle,
    error: FileWarning,
  };

  const severity = (alert.severity || 'info') as keyof typeof severityStyles;
  const Icon = severityIcons[severity];

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg border',
        severityStyles[severity]
      )}
    >
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <p className="text-sm">{alert.message}</p>
    </div>
  );
}

// Loading skeleton
function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-64" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-200 rounded-xl" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="h-80 bg-gray-200 rounded-xl" />
        <div className="h-80 bg-gray-200 rounded-xl lg:col-span-2" />
      </div>
    </div>
  );
}
