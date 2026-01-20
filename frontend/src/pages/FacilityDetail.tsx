import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Building2,
  MapPin,
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Calendar,
  Flame,
  Wind,
  Droplets,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../lib/api';
import { cn } from '../lib/utils';
import GapCard from '../components/GapCard';

export default function FacilityDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: facility, isLoading } = useQuery({
    queryKey: ['facility', id],
    queryFn: () => api.getFacility(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="h-64 bg-gray-200 rounded-xl" />
      </div>
    );
  }

  if (!facility) {
    return (
      <div className="text-center py-12">
        <Building2 className="w-12 h-12 text-gray-300 mx-auto" />
        <h2 className="mt-4 text-lg font-medium text-gray-900">
          Facility not found
        </h2>
        <Link
          to="/facilities"
          className="mt-4 text-emerald-600 hover:text-emerald-700"
        >
          ← Back to facilities
        </Link>
      </div>
    );
  }

  const metadata = facility.metadata ?? {};
  const emissions = metadata.total_potential_emissions_tpy ?? {};
  const sources = metadata.emission_sources ?? [];
  const permits = metadata.permits ?? [];

  const emissionsData = Object.entries(emissions).map(([pollutant, value]) => ({
    pollutant,
    value: value as number,
  }));

  // Mock gaps for this facility
  const facilityGaps = [
    {
      title: 'LDAR Survey Overdue',
      severity: 'critical' as const,
      deadline: '2025-01-15',
      regulation: '40 CFR 60.5397a',
    },
    {
      title: 'High-Bleed Pneumatic Controllers',
      severity: 'medium' as const,
      deadline: '2025-06-01',
      regulation: '40 CFR 60.5390a',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to="/facilities"
        className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to facilities
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center">
              <Building2 className="w-7 h-7 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{facility.name}</h1>
              <div className="flex items-center gap-2 mt-1 text-gray-500">
                <MapPin className="w-4 h-4" />
                <span>
                  {facility.county}, {facility.state}
                </span>
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                  {facility.facility_type}
                </span>
                {facility.is_major_source && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                    Major Source
                  </span>
                )}
                {facility.title_v_applicable && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                    Title V
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors">
              Run Analysis
            </button>
            <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
              Edit
            </button>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Compliance Score"
          value="82/100"
          icon={CheckCircle2}
          color="emerald"
        />
        <StatCard
          label="Open Gaps"
          value={facilityGaps.length.toString()}
          icon={AlertTriangle}
          color="amber"
        />
        <StatCard
          label="Emission Sources"
          value={sources.length.toString()}
          icon={Flame}
          color="orange"
        />
        <StatCard
          label="Active Permits"
          value={permits.length.toString()}
          icon={FileText}
          color="blue"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Emissions chart */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Potential Emissions (tons/year)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={emissionsData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" stroke="#9ca3af" fontSize={12} />
                <YAxis
                  dataKey="pollutant"
                  type="category"
                  stroke="#9ca3af"
                  fontSize={12}
                  width={60}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Permits */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Permits</h3>
          <div className="space-y-3">
            {permits.length > 0 ? (
              permits.map((permit: any, index: number) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-100"
                >
                  <div className="font-medium text-gray-900">
                    {permit.permit_number}
                  </div>
                  <div className="text-sm text-gray-500">{permit.permit_type}</div>
                  <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                    <Calendar className="w-3 h-3" />
                    Expires: {permit.expiration_date}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">No permits on file</p>
            )}
          </div>
        </div>
      </div>

      {/* Emission sources */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Emission Sources
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.length > 0 ? (
            sources.map((source: any) => (
              <div
                key={source.id}
                className="p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex items-center gap-2 mb-2">
                  {source.source_type === 'combustion' ? (
                    <Flame className="w-4 h-4 text-orange-500" />
                  ) : source.source_type === 'fugitive' ? (
                    <Wind className="w-4 h-4 text-blue-500" />
                  ) : (
                    <Droplets className="w-4 h-4 text-cyan-500" />
                  )}
                  <span className="font-medium text-gray-900">{source.name}</span>
                </div>
                <div className="text-sm text-gray-500">{source.equipment_type}</div>
                <div className="flex items-center gap-2 mt-2">
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded-full text-xs',
                      source.controlled
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-gray-100 text-gray-600'
                    )}
                  >
                    {source.controlled ? 'Controlled' : 'Uncontrolled'}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-sm col-span-full">
              No emission sources documented
            </p>
          )}
        </div>
      </div>

      {/* Compliance gaps */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Compliance Gaps</h3>
          <Link
            to="/gaps"
            className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
          >
            View all →
          </Link>
        </div>
        <div className="space-y-3">
          {facilityGaps.map((gap, index) => (
            <GapCard key={index} {...gap} facility={facility.name} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  icon: any;
  color: string;
}) {
  const colorStyles: Record<string, string> = {
    emerald: 'bg-emerald-100 text-emerald-600',
    amber: 'bg-amber-100 text-amber-600',
    orange: 'bg-orange-100 text-orange-600',
    blue: 'bg-blue-100 text-blue-600',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center', colorStyles[color])}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        <div className="text-sm text-gray-500">{label}</div>
      </div>
    </div>
  );
}
