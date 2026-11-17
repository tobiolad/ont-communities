const currencyFormatter = new Intl.NumberFormat("en-CA", {
  style: "currency",
  currency: "CAD",
  maximumFractionDigits: 0,
});

const compactCurrencyFormatter = new Intl.NumberFormat("en-CA", {
  style: "currency",
  currency: "CAD",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatCurrency(value: number | null | undefined, compact = false): string {
  if (value === null || value === undefined) return "Not disclosed";
  return (compact ? compactCurrencyFormatter : currencyFormatter).format(value);
}

export function formatBudgetCell(value: number, undisclosed: boolean): string {
  if (undisclosed) return "Not disclosed";
  return currencyFormatter.format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-CA").format(value);
}

export function formatPercent(part: number, total: number, digits = 1): string {
  if (total === 0) return "—";
  return `${((100 * part) / total).toFixed(digits)}%`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-CA", { year: "numeric", month: "short", day: "numeric" });
}
