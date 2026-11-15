const TONE: Record<string, string> = {
  high: "bg-emerald-50 text-signal-high border-emerald-200",
  medium: "bg-amber-50 text-signal-medium border-amber-200",
  low: "bg-red-50 text-signal-low border-red-200",
  info: "bg-blue-50 text-signal-info border-blue-200",
  neutral: "bg-canvas text-ink-secondary border-border",
};

const STATUS_TONE: Record<string, string> = {
  Complete: "high",
  "Under construction": "info",
  Planning: "medium",
};

export function Badge({ label, tone = "neutral" }: { label: string; tone?: keyof typeof TONE }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${TONE[tone]}`}>
      {label}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge label={status} tone={(STATUS_TONE[status] as keyof typeof TONE) || "neutral"} />;
}
