interface DataFieldProps {
  label: string;
  value: string | null | undefined;
  className?: string;
}

export function DataField({ label, value, className = "" }: DataFieldProps) {
  return (
    <div className={`${className}`}>
      <dt className="text-sm text-[var(--color-text-muted)]">{label}</dt>
      <dd className="mt-0.5 text-sm font-medium text-[var(--color-text-primary)]">
        {value ?? "-"}
      </dd>
    </div>
  );
}