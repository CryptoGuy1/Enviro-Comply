import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  PlayCircle,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Building2,
  FileText,
  Clock,
  ChevronRight,
} from 'lucide-react';
import { api } from '../lib/api';
import { cn } from '../lib/utils';

type AnalysisMode = 'full' | 'monitor' | 'gaps' | 'report';

interface AnalysisStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  result?: any;
}

export default function Analysis() {
  const [mode, setMode] = useState<AnalysisMode>('full');
  const [selectedFacilities, setSelectedFacilities] = useState<string[]>([]);
  const [steps, setSteps] = useState<AnalysisStep[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const { data: facilities } = useQuery({
    queryKey: ['facilities'],
    queryFn: api.getFacilities,
  });

  const runAnalysis = useMutation({
    mutationFn: async () => {
      setIsRunning(true);
      
      // Initialize steps based on mode
      const initialSteps = getStepsForMode(mode);
      setSteps(initialSteps);

      // Simulate step-by-step execution
      for (let i = 0; i < initialSteps.length; i++) {
        setSteps((prev) =>
          prev.map((step, idx) =>
            idx === i ? { ...step, status: 'running' } : step
          )
        );

        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 2000 + Math.random() * 1000));

        // Mark as completed with mock results
        setSteps((prev) =>
          prev.map((step, idx) =>
            idx === i
              ? {
                  ...step,
                  status: 'completed',
                  result: getMockResult(step.id),
                }
              : step
          )
        );
      }

      setIsRunning(false);
      return { success: true };
    },
  });

  const handleFacilityToggle = (facilityId: string) => {
    setSelectedFacilities((prev) =>
      prev.includes(facilityId)
        ? prev.filter((id) => id !== facilityId)
        : [...prev, facilityId]
    );
  };

  const handleSelectAll = () => {
    if (selectedFacilities.length === (facilities?.length ?? 0)) {
      setSelectedFacilities([]);
    } else {
      setSelectedFacilities((facilities ?? []).map((f: any) => f.facility_id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Run Analysis</h1>
        <p className="text-gray-500 mt-1">
          Execute compliance analysis using AI agents
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Analysis mode selection */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Analysis Mode
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <ModeCard
                id="full"
                name="Full Analysis"
                description="Complete compliance check"
                icon={PlayCircle}
                selected={mode === 'full'}
                onClick={() => setMode('full')}
              />
              <ModeCard
                id="monitor"
                name="Monitor"
                description="Scan for new regulations"
                icon={AlertTriangle}
                selected={mode === 'monitor'}
                onClick={() => setMode('monitor')}
              />
              <ModeCard
                id="gaps"
                name="Gap Analysis"
                description="Identify compliance gaps"
                icon={FileText}
                selected={mode === 'gaps'}
                onClick={() => setMode('gaps')}
              />
              <ModeCard
                id="report"
                name="Generate Report"
                description="Create compliance report"
                icon={FileText}
                selected={mode === 'report'}
                onClick={() => setMode('report')}
              />
            </div>
          </div>

          {/* Facility selection */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Select Facilities
              </h3>
              <button
                onClick={handleSelectAll}
                className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
              >
                {selectedFacilities.length === (facilities?.length ?? 0)
                  ? 'Deselect All'
                  : 'Select All'}
              </button>
            </div>
            <div className="space-y-2">
              {(facilities ?? []).map((facility: any) => (
                <label
                  key={facility.facility_id}
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all',
                    selectedFacilities.includes(facility.facility_id)
                      ? 'border-emerald-500 bg-emerald-50'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                >
                  <input
                    type="checkbox"
                    checked={selectedFacilities.includes(facility.facility_id)}
                    onChange={() => handleFacilityToggle(facility.facility_id)}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  <Building2 className="w-5 h-5 text-gray-400" />
                  <div>
                    <div className="font-medium text-gray-900">
                      {facility.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {facility.facility_type} • {facility.state}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Run button */}
          <button
            onClick={() => runAnalysis.mutate()}
            disabled={isRunning || selectedFacilities.length === 0}
            className={cn(
              'w-full py-4 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2',
              isRunning || selectedFacilities.length === 0
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-700'
            )}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Running Analysis...
              </>
            ) : (
              <>
                <PlayCircle className="w-5 h-5" />
                Run {mode === 'full' ? 'Full ' : ''}Analysis
              </>
            )}
          </button>
        </div>

        {/* Progress panel */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Analysis Progress
          </h3>

          {steps.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="w-12 h-12 text-gray-300 mx-auto" />
              <p className="mt-4 text-gray-500">
                Configure and run an analysis to see progress
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={step.id} className="relative">
                  {index < steps.length - 1 && (
                    <div
                      className={cn(
                        'absolute left-4 top-10 w-0.5 h-full -ml-px',
                        step.status === 'completed'
                          ? 'bg-emerald-500'
                          : 'bg-gray-200'
                      )}
                    />
                  )}
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                        step.status === 'completed'
                          ? 'bg-emerald-100'
                          : step.status === 'running'
                          ? 'bg-blue-100'
                          : step.status === 'error'
                          ? 'bg-red-100'
                          : 'bg-gray-100'
                      )}
                    >
                      {step.status === 'completed' ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      ) : step.status === 'running' ? (
                        <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                      ) : step.status === 'error' ? (
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                      ) : (
                        <div className="w-2 h-2 rounded-full bg-gray-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900">{step.name}</div>
                      <div className="text-sm text-gray-500">
                        {step.description}
                      </div>
                      {step.result && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
                          {typeof step.result === 'string'
                            ? step.result
                            : JSON.stringify(step.result)}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {steps.length > 0 && !isRunning && (
            <div className="mt-6 pt-4 border-t border-gray-100">
              <a
                href="/gaps"
                className="flex items-center justify-between text-sm text-emerald-600 hover:text-emerald-700 font-medium"
              >
                View Results
                <ChevronRight className="w-4 h-4" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ModeCard({
  id,
  name,
  description,
  icon: Icon,
  selected,
  onClick,
}: {
  id: string;
  name: string;
  description: string;
  icon: any;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'p-4 rounded-lg border-2 text-left transition-all',
        selected
          ? 'border-emerald-500 bg-emerald-50'
          : 'border-gray-200 hover:border-gray-300'
      )}
    >
      <Icon
        className={cn(
          'w-6 h-6 mb-2',
          selected ? 'text-emerald-600' : 'text-gray-400'
        )}
      />
      <div className="font-medium text-gray-900">{name}</div>
      <div className="text-xs text-gray-500 mt-1">{description}</div>
    </button>
  );
}

function getStepsForMode(mode: AnalysisMode): AnalysisStep[] {
  const steps: Record<AnalysisMode, AnalysisStep[]> = {
    full: [
      {
        id: 'monitor',
        name: 'Regulation Monitoring',
        description: 'Scanning EPA and state sources...',
        status: 'pending',
      },
      {
        id: 'assess',
        name: 'Impact Assessment',
        description: 'Mapping regulations to facilities...',
        status: 'pending',
      },
      {
        id: 'analyze',
        name: 'Gap Analysis',
        description: 'Identifying compliance gaps...',
        status: 'pending',
      },
      {
        id: 'report',
        name: 'Report Generation',
        description: 'Creating compliance report...',
        status: 'pending',
      },
    ],
    monitor: [
      {
        id: 'monitor',
        name: 'Regulation Monitoring',
        description: 'Scanning EPA and state sources...',
        status: 'pending',
      },
    ],
    gaps: [
      {
        id: 'assess',
        name: 'Impact Assessment',
        description: 'Mapping regulations to facilities...',
        status: 'pending',
      },
      {
        id: 'analyze',
        name: 'Gap Analysis',
        description: 'Identifying compliance gaps...',
        status: 'pending',
      },
    ],
    report: [
      {
        id: 'report',
        name: 'Report Generation',
        description: 'Creating compliance report...',
        status: 'pending',
      },
    ],
  };
  return steps[mode];
}

function getMockResult(stepId: string): string {
  const results: Record<string, string> = {
    monitor: 'Found 2 new regulations, 1 amendment',
    assess: 'Assessed 3 facilities, 2 high-impact',
    analyze: 'Identified 5 gaps (1 critical, 2 high)',
    report: 'Report generated: gap_analysis_20250107.pdf',
  };
  return results[stepId] ?? 'Completed';
}
