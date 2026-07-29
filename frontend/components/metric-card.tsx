import { Card } from "@/components/ui/card";

interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
  className?: string;
}

export function MetricCard({ label, value, unit, className = "" }: MetricCardProps) {
  return (
    <Card className={`text-center ${className}`}>
      <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
      <p className="mt-1 text-2xl font-bold text-[var(--color-text-primary)]">
        {value}
      </p>
      {unit && (
        <p className="text-xs text-[var(--color-text-secondary)]">{unit}</p>
      )}
    </Card>
  );
}