import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num);
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'red',
    high: 'orange',
    medium: 'yellow',
    low: 'green',
  };
  return colors[severity] ?? 'gray';
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    open: 'gray',
    in_progress: 'blue',
    pending_verification: 'amber',
    closed: 'emerald',
    deferred: 'purple',
  };
  return colors[status] ?? 'gray';
}
