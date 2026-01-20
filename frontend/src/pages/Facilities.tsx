import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Building2,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Plus,
  Search,
  Filter,
} from 'lucide-react';
import { useState } from 'react';
import { api } from '../lib/api';
import { cn } from '../lib/utils';

export default function Facilities() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterState, setFilterState] = useState<string>('all');

  const { data: facilities, isLoading } = useQuery({
    queryKey: ['facilities'],
    queryFn: api.getFacilities,
  });

  const filteredFacilities = (facilities ?? []).filter((facility: any) => {
    const matchesSearch =
      facility.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      facility.operator?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesState =
      filterState === 'all' || facility.state === filterState;
    return matchesSearch && matchesState;
  });

  const states = [...new Set((facilities ?? []).map((f: any) => f.state))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Facilities</h1>
          <p className="text-gray-500 mt-1">
            Manage and monitor your Oil & Gas facilities
          </p>
        </div>
        <button className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors">
          <Plus className="w-4 h-4" />
          Add Facility
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search facilities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={filterState}
            onChange={(e) => setFilterState(e.target.value)}
            className="pl-10 pr-8 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none bg-white"
          >
            <option value="all">All States</option>
            {states.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Facilities grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-gray-200 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredFacilities.map((facility: any) => (
            <FacilityCard key={facility.facility_id} facility={facility} />
          ))}
        </div>
      )}

      {filteredFacilities.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 text-gray-300 mx-auto" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            No facilities found
          </h3>
          <p className="mt-2 text-gray-500">
            {searchQuery || filterState !== 'all'
              ? 'Try adjusting your search or filters'
              : 'Get started by adding your first facility'}
          </p>
        </div>
      )}
    </div>
  );
}

function FacilityCard({ facility }: { facility: any }) {
  const metadata = facility.metadata ?? {};
  const emissions = metadata.total_potential_emissions_tpy ?? {};
  const gapCount = Math.floor(Math.random() * 5); // Mock data
  const hasIssues = gapCount > 0;

  const facilityTypeLabels: Record<string, string> = {
    production: 'Production Site',
    gathering: 'Gathering Station',
    processing: 'Gas Processing',
    transmission: 'Transmission',
    storage: 'Storage Terminal',
  };

  return (
    <Link
      to={`/facilities/${facility.facility_id}`}
      className="block bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:border-emerald-200 transition-all"
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center',
                hasIssues ? 'bg-amber-100' : 'bg-emerald-100'
              )}
            >
              <Building2
                className={cn(
                  'w-5 h-5',
                  hasIssues ? 'text-amber-600' : 'text-emerald-600'
                )}
              />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{facility.name}</h3>
              <p className="text-sm text-gray-500">
                {facilityTypeLabels[facility.facility_type] ?? facility.facility_type}
              </p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </div>

        {/* Location */}
        <div className="flex items-center gap-1.5 mt-4 text-sm text-gray-600">
          <MapPin className="w-4 h-4" />
          <span>
            {facility.county}, {facility.state}
          </span>
        </div>

        {/* Status badges */}
        <div className="flex flex-wrap gap-2 mt-4">
          {facility.is_major_source && (
            <span className="px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-700 rounded-full">
              Major Source
            </span>
          )}
          {facility.title_v_applicable && (
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
              Title V
            </span>
          )}
        </div>

        {/* Compliance status */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1.5">
            {hasIssues ? (
              <>
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span className="text-sm text-amber-600">
                  {gapCount} open gap{gapCount !== 1 ? 's' : ''}
                </span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span className="text-sm text-emerald-600">Compliant</span>
              </>
            )}
          </div>
          <span className="text-xs text-gray-400">
            {facility.operator}
          </span>
        </div>
      </div>
    </Link>
  );
}
