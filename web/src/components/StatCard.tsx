export function StatCard({ label, value, sublabel }: { label: string; value: string | number; sublabel?: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="text-2xl font-bold text-ink-primary">{value}</div>
      <div className="mt-1 text-sm font-medium text-ink-secondary">{label}</div>
      {sublabel && <div className="mt-0.5 text-xs text-ink-muted">{sublabel}</div>}
    </div>
  );
}
