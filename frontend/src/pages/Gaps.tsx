import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
  AlertTriangle,
  Search,
  Filter,
  ChevronDown,
  Clock,
  DollarSign,
  Building2,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../lib/api';
import { cn } from '../lib/utils';
import { format, parseISO, differenceInDays } from 'date-fns';

type Severity = 'all' | 'critical' | 'high' | 'medium' | 'low';
type Status = 'all' | 'open' | 'in_progress' | 'closed';

export default function Gaps() {
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<Severity>('all');
  const [statusFilter, setStatusFilter] = useState<Status>('all');
  const [expandedGap, setExpandedGap] = useState<string | null>(null);

  const { data: gapsData, isLoading } = useQuery({
    queryKey: ['gaps'],
    queryFn: api.getGaps,
  });

  // Mock gaps data if API doesn't return
  const gaps = gapsData?.gaps ?? getMockGaps();
  const summary = gapsData?.summary ?? {
    critical: gaps.filter((g: any) => g.severity === 'critical').length,
    high: gaps.filter((g: any) => g.severity === 'high').length,
    medium: gaps.filter((g: any) => g.severity === 'medium').length,
    low: gaps.filter((g: any) => g.severity === 'low').length,
    total: gaps.length,
  };

  const filteredGaps = gaps.filter((gap: any) => {
    const matchesSearch =
      gap.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      gap.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity =
      severityFilter === 'all' || gap.severity === severityFilter;
    const matchesStatus =
      statusFilter === 'all' || gap.status === statusFilter;
    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const totalCost = filteredGaps.reduce(
    (sum: number, gap: any) => sum + (gap.estimated_cost ?? 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Gaps</h1>
        <p className="text-gray-500 mt-1">
          Track and remediate compliance gaps across all facilities
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <SummaryCard
          label="Critical"
          count={summary.critical}
          color="red"
          active={severityFilter === 'critical'}
          onClick={() =>
            setSeverityFilter(severityFilter === 'critical' ? 'all' : 'critical')
          }
        />
        <SummaryCard
          label="High"
          count={summary.high}
          color="orange"
          active={severityFilter === 'high'}
          onClick={() =>
            setSeverityFilter(severityFilter === 'high' ? 'all' : 'high')
          }
        />
        <SummaryCard
          label="Medium"
          count={summary.medium}
          color="yellow"
          active={severityFilter === 'medium'}
          onClick={() =>
            setSeverityFilter(severityFilter === 'medium' ? 'all' : 'medium')
          }
        />
        <SummaryCard
          label="Low"
          count={summary.low}
          color="green"
          active={severityFilter === 'low'}
          onClick={() =>
            setSeverityFilter(severityFilter === 'low' ? 'all' : 'low')
          }
        />
        <SummaryCard
          label="Total"
          count={summary.total}
          color="gray"
          active={severityFilter === 'all'}
          onClick={() => setSeverityFilter('all')}
        />
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search gaps..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as Status)}
          className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
        >
          <option value="all">All Status</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {/* Cost summary */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-amber-600" />
          <span className="text-amber-800">
            Estimated remediation cost for filtered gaps:
          </span>
        </div>
        <span className="text-lg font-bold text-amber-900">
          ${totalCost.toLocaleString()}
        </span>
      </div>

      {/* Gaps list */}
      <div className="space-y-4">
        {isLoading ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg animate-pulse" />
          ))
        ) : filteredGaps.length > 0 ? (
          filteredGaps.map((gap: any) => (
            <GapItem
              key={gap.id}
              gap={gap}
              isExpanded={expandedGap === gap.id}
              onToggle={() =>
                setExpandedGap(expandedGap === gap.id ? null : gap.id)
              }
            />
          ))
        ) : (
          <div className="text-center py-12">
            <CheckCircle2 className="w-12 h-12 text-emerald-300 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No gaps found
            </h3>
            <p className="mt-2 text-gray-500">
              {searchQuery || severityFilter !== 'all' || statusFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'All compliance requirements are being met'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  count,
  color,
  active,
  onClick,
}: {
  label: string;
  count: number;
  color: string;
  active: boolean;
  onClick: () => void;
}) {
  const colorStyles: Record<string, string> = {
    red: 'bg-red-50 border-red-200 text-red-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    gray: 'bg-gray-50 border-gray-200 text-gray-700',
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'p-4 rounded-lg border-2 transition-all text-left',
        colorStyles[color],
        active && 'ring-2 ring-offset-2 ring-emerald-500'
      )}
    >
      <div className="text-2xl font-bold">{count}</div>
      <div className="text-sm">{label}</div>
    </button>
  );
}

function GapItem({
  gap,
  isExpanded,
  onToggle,
}: {
  gap: any;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const severityStyles: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-orange-100 text-orange-700 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    low: 'bg-green-100 text-green-700 border-green-200',
  };

  const statusStyles: Record<string, string> = {
    open: 'bg-gray-100 text-gray-700',
    in_progress: 'bg-blue-100 text-blue-700',
    closed: 'bg-emerald-100 text-emerald-700',
  };

  const daysUntil = gap.regulatory_deadline
    ? differenceInDays(parseISO(gap.regulatory_deadline), new Date())
    : null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-start justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-start gap-4">
          <AlertTriangle
            className={cn(
              'w-5 h-5 mt-0.5',
              gap.severity === 'critical'
                ? 'text-red-500'
                : gap.severity === 'high'
                ? 'text-orange-500'
                : gap.severity === 'medium'
                ? 'text-yellow-500'
                : 'text-green-500'
            )}
          />
          <div>
            <h3 className="font-medium text-gray-900">{gap.title}</h3>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Building2 className="w-4 h-4" />
                {gap.facility_name ?? 'Facility'}
              </span>
              {gap.regulation_id && (
                <span className="flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" />
                  {gap.regulation_id}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={cn(
              'px-2 py-0.5 rounded-full text-xs font-medium uppercase',
              severityStyles[gap.severity]
            )}
          >
            {gap.severity}
          </span>
          <span
            className={cn(
              'px-2 py-0.5 rounded-full text-xs font-medium',
              statusStyles[gap.status]
            )}
          >
            {gap.status.replace('_', ' ')}
          </span>
          <ChevronDown
            className={cn(
              'w-5 h-5 text-gray-400 transition-transform',
              isExpanded && 'rotate-180'
            )}
          />
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Description
              </h4>
              <p className="text-sm text-gray-600">{gap.description}</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Recommended Action
              </h4>
              <p className="text-sm text-gray-600">{gap.recommended_action}</p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap items-center gap-6 text-sm">
            {gap.regulatory_deadline && (
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">
                  Deadline: {format(parseISO(gap.regulatory_deadline), 'MMM d, yyyy')}
                  {daysUntil !== null && (
                    <span
                      className={cn(
                        'ml-2',
                        daysUntil < 0
                          ? 'text-red-600'
                          : daysUntil < 30
                          ? 'text-amber-600'
                          : 'text-gray-500'
                      )}
                    >
                      ({daysUntil < 0
                        ? `${Math.abs(daysUntil)} days overdue`
                        : `${daysUntil} days remaining`})
                    </span>
                  )}
                </span>
              </div>
            )}
            {gap.estimated_cost && (
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">
                  Est. Cost: ${gap.estimated_cost.toLocaleString()}
                </span>
              </div>
            )}
            {gap.risk_score && (
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">
                  Risk Score: {(gap.risk_score * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>

          <div className="mt-4 flex gap-2">
            <button className="px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors">
              Mark Resolved
            </button>
            <button className="px-4 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors">
              Assign
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function getMockGaps() {
  return [
    {
      id: 'gap-001',
      title: 'LDAR Survey Overdue',
      description:
        'Last LDAR survey was 95 days ago. Quarterly surveys required under NSPS OOOOa for wellhead and compressor components.',
      severity: 'critical',
      status: 'open',
      facility_name: 'Permian Basin Production Facility 1',
      regulation_id: '40 CFR 60.5397a',
      recommended_action:
        'Conduct LDAR survey immediately. Schedule remaining quarterly surveys for the year.',
      estimated_cost: 5000,
      risk_score: 0.95,
      regulatory_deadline: '2025-01-15',
    },
    {
      id: 'gap-002',
      title: 'High-Bleed Pneumatic Controllers',
      description:
        'Found 3 high-bleed pneumatic controllers. NSPS OOOOb requires low-bleed or zero-emission controllers at wellsites.',
      severity: 'high',
      status: 'in_progress',
      facility_name: 'Bakken Gathering Station',
      regulation_id: '40 CFR 60.5390a',
      recommended_action:
        'Replace high-bleed controllers with low-bleed (<6 scfh) or zero-emission alternatives.',
      estimated_cost: 7500,
      risk_score: 0.75,
      regulatory_deadline: '2025-03-01',
    },
    {
      id: 'gap-003',
      title: 'Permit Expiring Soon',
      description:
        'Title V permit WY-TV-2020-005 expires in 75 days. Most agencies require 6+ months notice for renewal.',
      severity: 'high',
      status: 'open',
      facility_name: 'Wyoming Gas Processing Plant',
      regulation_id: 'Title V',
      recommended_action:
        'Initiate permit renewal process immediately. Gather emissions data and prepare renewal application.',
      estimated_cost: 15000,
      risk_score: 0.7,
      regulatory_deadline: '2025-03-15',
    },
    {
      id: 'gap-004',
      title: 'Uncontrolled Glycol Dehydrator',
      description:
        'Glycol dehydrator lacks emission controls. NESHAP HH requires HAP controls for major sources.',
      severity: 'medium',
      status: 'open',
      facility_name: 'Bakken Gathering Station',
      regulation_id: '40 CFR 63 Subpart HH',
      recommended_action:
        'Install condenser or reboiler vent controls. Consider flash tank or BTEX recovery.',
      estimated_cost: 50000,
      risk_score: 0.55,
      regulatory_deadline: '2025-06-01',
    },
    {
      id: 'gap-005',
      title: 'GHG Reporting Documentation Gap',
      description:
        'Missing calculation methodology documentation for some emission sources in Subpart W report.',
      severity: 'low',
      status: 'open',
      facility_name: 'Wyoming Gas Processing Plant',
      regulation_id: '40 CFR 98 Subpart W',
      recommended_action:
        'Document emission calculation methodologies for all sources. Update procedures before annual report.',
      estimated_cost: 2500,
      risk_score: 0.25,
      regulatory_deadline: '2025-03-31',
    },
  ];
}
