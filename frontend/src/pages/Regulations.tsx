import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ScrollText,
  Search,
  ExternalLink,
  Calendar,
  Building2,
  ChevronDown,
  Filter,
} from 'lucide-react';
import { api } from '../lib/api';
import { cn } from '../lib/utils';

export default function Regulations() {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [expandedReg, setExpandedReg] = useState<string | null>(null);

  // Mock regulations data
  const regulations = [
    {
      id: 'nsps-ooooa',
      citation: '40 CFR 60 Subpart OOOOa',
      title: 'Standards of Performance for Crude Oil and Natural Gas Facilities',
      regulation_type: 'nsps',
      status: 'effective',
      description:
        'Establishes emission standards for VOC and methane from affected facilities in the crude oil and natural gas source category.',
      effective_date: '2016-08-02',
      applicable_facility_types: ['production', 'gathering', 'processing', 'transmission'],
      key_requirements: [
        'Reduce VOC emissions from storage vessels by 95%',
        'Use low-bleed or no-bleed pneumatic controllers',
        'Conduct LDAR surveys at wellsites and compressor stations',
        'Control emissions from centrifugal compressors',
        'Monitor and repair fugitive emissions',
      ],
    },
    {
      id: 'nsps-oooob',
      citation: '40 CFR 60 Subpart OOOOb',
      title: 'Standards of Performance for GHG and VOC Emissions',
      regulation_type: 'nsps',
      status: 'effective',
      description:
        'Updates and strengthens standards for new and modified sources, adding super-emitter response program.',
      effective_date: '2024-05-07',
      applicable_facility_types: ['production', 'gathering', 'processing', 'transmission'],
      key_requirements: [
        'Zero-emission pneumatic controllers at new sites',
        'Enhanced LDAR requirements',
        'Super-emitter response program participation',
        'Reduced emissions during liquids unloading',
        'Flare efficiency requirements',
      ],
    },
    {
      id: 'neshap-hh',
      citation: '40 CFR 63 Subpart HH',
      title: 'NESHAP for Oil and Natural Gas Production Facilities',
      regulation_type: 'neshap',
      status: 'effective',
      description:
        'Establishes HAP emission standards for major sources in oil and natural gas production.',
      effective_date: '1999-06-17',
      applicable_facility_types: ['production', 'processing'],
      key_requirements: [
        'HAP emission reduction from glycol dehydrators',
        'Triethylene glycol (TEG) dehydrator controls',
        'Small glycol dehydrator exemptions',
        'Initial notification and compliance reports',
      ],
    },
    {
      id: 'ghg-subpart-w',
      citation: '40 CFR 98 Subpart W',
      title: 'Petroleum and Natural Gas Systems - GHG Reporting',
      regulation_type: 'ghg_reporting',
      status: 'effective',
      description:
        'Requires annual GHG reporting from facilities exceeding 25,000 MT CO2e.',
      effective_date: '2010-12-01',
      applicable_facility_types: ['production', 'gathering', 'processing', 'transmission'],
      key_requirements: [
        'Calculate GHG emissions using specified methods',
        'Report annually by March 31',
        'Maintain records for 3 years',
        'Use electronic reporting (e-GGRT)',
      ],
    },
  ];

  const filteredRegulations = regulations.filter((reg) => {
    const matchesSearch =
      reg.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      reg.citation.toLowerCase().includes(searchQuery.toLowerCase()) ||
      reg.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType =
      typeFilter === 'all' || reg.regulation_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const typeLabels: Record<string, string> = {
    nsps: 'NSPS',
    neshap: 'NESHAP',
    ghg_reporting: 'GHG Reporting',
    sip: 'State Implementation',
    title_v: 'Title V',
    state: 'State',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulations</h1>
        <p className="text-gray-500 mt-1">
          Browse and search EPA and state environmental regulations
        </p>
      </div>

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search regulations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
        >
          <option value="all">All Types</option>
          <option value="nsps">NSPS</option>
          <option value="neshap">NESHAP</option>
          <option value="ghg_reporting">GHG Reporting</option>
          <option value="state">State</option>
        </select>
      </div>

      {/* Regulations list */}
      <div className="space-y-4">
        {filteredRegulations.map((reg) => (
          <div
            key={reg.id}
            className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
          >
            <button
              onClick={() =>
                setExpandedReg(expandedReg === reg.id ? null : reg.id)
              }
              className="w-full p-5 flex items-start justify-between text-left hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <ScrollText className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                      {reg.citation}
                    </span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded-full text-xs font-medium',
                        reg.regulation_type === 'nsps'
                          ? 'bg-blue-100 text-blue-700'
                          : reg.regulation_type === 'neshap'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-gray-100 text-gray-700'
                      )}
                    >
                      {typeLabels[reg.regulation_type] ?? reg.regulation_type}
                    </span>
                  </div>
                  <h3 className="font-medium text-gray-900 mt-1">{reg.title}</h3>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {reg.description}
                  </p>
                </div>
              </div>
              <ChevronDown
                className={cn(
                  'w-5 h-5 text-gray-400 transition-transform flex-shrink-0',
                  expandedReg === reg.id && 'rotate-180'
                )}
              />
            </button>

            {expandedReg === reg.id && (
              <div className="px-5 pb-5 border-t border-gray-100">
                <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Key requirements */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Key Requirements
                    </h4>
                    <ul className="space-y-2">
                      {reg.key_requirements.map((req, index) => (
                        <li
                          key={index}
                          className="flex items-start gap-2 text-sm text-gray-600"
                        >
                          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1.5 flex-shrink-0" />
                          {req}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Details */}
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Applicable Facility Types
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {reg.applicable_facility_types.map((type) => (
                          <span
                            key={type}
                            className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                          >
                            <Building2 className="w-3 h-3" />
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        Effective Date
                      </h4>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        {reg.effective_date}
                      </div>
                    </div>

                    <a
                      href={`https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-60`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-emerald-600 hover:text-emerald-700"
                    >
                      View on eCFR
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
