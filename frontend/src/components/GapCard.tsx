import { AlertTriangle, Clock, Building2, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';
import { format, differenceInDays, parseISO } from 'date-fns';

interface GapCardProps {
  title: string;
  facility: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  deadline?: string;
  regulation?: string;
  onClick?: () => void;
}

export default function GapCard({
  title,
  facility,
  severity,
  deadline,
  regulation,
  onClick,
}: GapCardProps) {
  const severityConfig = {
    critical: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      badge: 'bg-red-100 text-red-700',
      icon: 'text-red-500',
    },
    high: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      badge: 'bg-orange-100 text-orange-700',
      icon: 'text-orange-500',
    },
    medium: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      badge: 'bg-yellow-100 text-yellow-700',
      icon: 'text-yellow-500',
    },
    low: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      badge: 'bg-green-100 text-green-700',
      icon: 'text-green-500',
    },
  };

  const config = severityConfig[severity];
  
  const daysUntilDeadline = deadline
    ? differenceInDays(parseISO(deadline), new Date())
    : null;

  return (
    <div
      className={cn(
        'p-4 rounded-lg border transition-all cursor-pointer hover:shadow-md',
        config.bg,
        config.border
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className={cn('w-5 h-5 mt-0.5', config.icon)} />
          <div>
            <h4 className="font-medium text-gray-900">{title}</h4>
            <div className="flex items-center gap-2 mt-1 text-sm text-gray-600">
              <Building2 className="w-4 h-4" />
              <span>{facility}</span>
            </div>
            {regulation && (
              <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                <ExternalLink className="w-3 h-3" />
                <span>{regulation}</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-2">
          <span
            className={cn(
              'px-2 py-0.5 rounded-full text-xs font-medium uppercase',
              config.badge
            )}
          >
            {severity}
          </span>
          
          {deadline && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span>
                {daysUntilDeadline !== null && daysUntilDeadline >= 0
                  ? `${daysUntilDeadline} days`
                  : daysUntilDeadline !== null
                  ? `${Math.abs(daysUntilDeadline)} days overdue`
                  : format(parseISO(deadline), 'MMM d, yyyy')}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
