export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 rounded-xl border border-border bg-surface px-5 py-8 text-sm text-ink-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand/30 border-t-brand" aria-hidden="true" />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-xl border border-signal-low/30 bg-red-50 px-5 py-4 text-sm text-signal-low">
      <p className="font-semibold">Couldn&apos;t load this data.</p>
      <p className="mt-1 text-ink-secondary">{message}</p>
    </div>
  );
}

export function EmptyState({ message = "No results match the current filters." }: { message?: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-surface px-5 py-12 text-center text-sm text-ink-muted">
      {message}
    </div>
  );
}

export function NoteBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-brand/20 bg-brand-dim px-4 py-3 text-sm text-ink-secondary">
      {children}
    </div>
  );
}
