import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  delta?: {
    value: string | number;
    positive?: boolean;
    label?: string;
  };
  mono?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  delta,
  mono = false,
}) => {
  return (
    <div className="flex flex-col justify-between p-4 bg-white rounded-lg border border-slate-200">
      <span className="text-xs font-medium text-slate-500 tracking-tight">{label}</span>
      <div className="mt-2 flex items-baseline justify-between gap-2">
        <span
          className={`text-2xl font-semibold text-slate-900 tracking-tight ${
            mono ? 'font-mono' : ''
          }`}
        >
          {value}
        </span>
        {delta && (
          <span
            className={`inline-flex items-center text-xs font-medium font-mono px-1.5 py-0.5 rounded ${
              delta.positive
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            {delta.positive ? '+' : ''}
            {delta.value} {delta.label && <span className="ml-1 text-[10px] text-slate-400">{delta.label}</span>}
          </span>
        )}
      </div>
      {subValue && <span className="mt-1 text-xs text-slate-400">{subValue}</span>}
    </div>
  );
};
