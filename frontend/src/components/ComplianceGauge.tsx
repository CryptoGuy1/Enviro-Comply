import { cn } from '../lib/utils';

interface ComplianceGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export default function ComplianceGauge({ score, size = 'md' }: ComplianceGaugeProps) {
  const sizes = {
    sm: { width: 120, strokeWidth: 8, fontSize: 'text-xl' },
    md: { width: 160, strokeWidth: 10, fontSize: 'text-3xl' },
    lg: { width: 200, strokeWidth: 12, fontSize: 'text-4xl' },
  };

  const { width, strokeWidth, fontSize } = sizes[size];
  const radius = (width - strokeWidth) / 2;
  const circumference = radius * Math.PI; // Half circle
  const progress = (score / 100) * circumference;

  const getColor = (score: number) => {
    if (score >= 90) return { stroke: '#10b981', text: 'text-emerald-500' };
    if (score >= 75) return { stroke: '#22c55e', text: 'text-green-500' };
    if (score >= 60) return { stroke: '#eab308', text: 'text-yellow-500' };
    if (score >= 40) return { stroke: '#f97316', text: 'text-orange-500' };
    return { stroke: '#ef4444', text: 'text-red-500' };
  };

  const { stroke, text } = getColor(score);

  return (
    <div className="relative inline-flex flex-col items-center">
      <svg
        width={width}
        height={width / 2 + 20}
        className="transform -rotate-0"
      >
        {/* Background arc */}
        <path
          d={`M ${strokeWidth / 2} ${width / 2} A ${radius} ${radius} 0 0 1 ${width - strokeWidth / 2} ${width / 2}`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d={`M ${strokeWidth / 2} ${width / 2} A ${radius} ${radius} 0 0 1 ${width - strokeWidth / 2} ${width / 2}`}
          fill="none"
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      
      {/* Score display */}
      <div className="absolute bottom-0 flex flex-col items-center">
        <span className={cn('font-bold', fontSize, text)}>{score}</span>
        <span className="text-xs text-gray-500 mt-1">out of 100</span>
      </div>

      {/* Scale markers */}
      <div className="absolute top-1/2 left-0 right-0 flex justify-between px-1 text-xs text-gray-400">
        <span>0</span>
        <span>100</span>
      </div>
    </div>
  );
}
