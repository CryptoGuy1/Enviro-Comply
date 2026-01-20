import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Calendar,
  Clock,
  Building2,
  Plus,
  Loader2,
  CheckCircle2,
} from 'lucide-react';
import { format } from 'date-fns';
import { api } from '../lib/api';
import { cn } from '../lib/utils';

const reportTypes = [
  {
    id: 'gap_analysis',
    name: 'Gap Analysis Report',
    description: 'Comprehensive compliance gap assessment',
  },
  {
    id: 'executive_summary',
    name: 'Executive Summary',
    description: 'High-level compliance overview for leadership',
  },
  {
    id: 'regulatory_briefing',
    name: 'Regulatory Briefing',
    description: 'Summary of recent regulatory changes',
  },
  {
    id: 'annual_certification',
    name: 'Annual Certification',
    description: 'Title V annual compliance certification',
  },
];

export default function Reports() {
  const [showGenerator, setShowGenerator] = useState(false);
  const [selectedType, setSelectedType] = useState('gap_analysis');
  const [selectedFacilities, setSelectedFacilities] = useState<string[]>([]);

  const { data: facilities } = useQuery({
    queryKey: ['facilities'],
    queryFn: api.getFacilities,
  });

  const generateReport = useMutation({
    mutationFn: api.generateReport,
    onSuccess: () => {
      setShowGenerator(false);
    },
  });

  // Mock recent reports
  const recentReports = [
    {
      id: 'rpt-001',
      title: 'Gap Analysis Report - December 2024',
      type: 'gap_analysis',
      generated_at: '2024-12-15T10:30:00Z',
      compliance_score: 85,
      facilities: ['Permian Basin Facility 1', 'Bakken Gathering Station'],
    },
    {
      id: 'rpt-002',
      title: 'Executive Summary - Q4 2024',
      type: 'executive_summary',
      generated_at: '2024-12-01T14:00:00Z',
      compliance_score: 82,
      facilities: ['All Facilities'],
    },
    {
      id: 'rpt-003',
      title: 'Regulatory Briefing - November 2024',
      type: 'regulatory_briefing',
      generated_at: '2024-11-20T09:15:00Z',
      regulations_covered: 5,
    },
  ];

  const handleGenerate = () => {
    generateReport.mutate({
      report_type: selectedType,
      facility_ids: selectedFacilities.length > 0 ? selectedFacilities : undefined,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-500 mt-1">
            Generate and manage compliance reports
          </p>
        </div>
        <button
          onClick={() => setShowGenerator(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Report
        </button>
      </div>

      {/* Report generator modal */}
      {showGenerator && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900">
                Generate New Report
              </h3>
            </div>

            <div className="p-6 space-y-4">
              {/* Report type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Type
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  {reportTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-sm text-gray-500">
                  {reportTypes.find((t) => t.id === selectedType)?.description}
                </p>
              </div>

              {/* Facility selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Facilities (optional)
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {(facilities ?? []).map((facility: any) => (
                    <label
                      key={facility.facility_id}
                      className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedFacilities.includes(facility.facility_id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedFacilities([
                              ...selectedFacilities,
                              facility.facility_id,
                            ]);
                          } else {
                            setSelectedFacilities(
                              selectedFacilities.filter(
                                (id) => id !== facility.facility_id
                              )
                            );
                          }
                        }}
                        className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                      />
                      <span className="text-sm text-gray-700">
                        {facility.name}
                      </span>
                    </label>
                  ))}
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Leave empty to include all facilities
                </p>
              </div>
            </div>

            <div className="p-6 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={() => setShowGenerator(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerate}
                disabled={generateReport.isPending}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {generateReport.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Generate Report
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Report types overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {reportTypes.map((type) => (
          <div
            key={type.id}
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-5"
          >
            <FileText className="w-8 h-8 text-emerald-500 mb-3" />
            <h3 className="font-semibold text-gray-900">{type.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{type.description}</p>
          </div>
        ))}
      </div>

      {/* Recent reports */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Recent Reports</h3>
        </div>
        <div className="divide-y divide-gray-100">
          {recentReports.map((report) => (
            <div
              key={report.id}
              className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{report.title}</h4>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {format(new Date(report.generated_at), 'MMM d, yyyy')}
                    </span>
                    {report.facilities && (
                      <span className="flex items-center gap-1">
                        <Building2 className="w-4 h-4" />
                        {report.facilities.length} facilities
                      </span>
                    )}
                    {report.compliance_score && (
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        Score: {report.compliance_score}/100
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <button className="p-2 text-gray-400 hover:text-emerald-600 transition-colors">
                <Download className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
