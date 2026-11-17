import { describe, it, expect } from "vitest";
import { formatCurrency, formatBudgetCell, formatPercent, formatNumber } from "./format";

describe("formatCurrency", () => {
  it("formats a positive number as whole-dollar CAD currency", () => {
    expect(formatCurrency(1500000)).toBe("$1,500,000");
  });

  it("returns 'Not disclosed' for null, never $0", () => {
    expect(formatCurrency(null)).toBe("Not disclosed");
  });

  it("returns 'Not disclosed' for undefined", () => {
    expect(formatCurrency(undefined)).toBe("Not disclosed");
  });

  it("supports compact notation", () => {
    expect(formatCurrency(7300000000, true)).toMatch(/\$7\.3B/);
  });
});

describe("formatBudgetCell", () => {
  it("shows 'Not disclosed' when the undisclosed flag is true, not $0", () => {
    expect(formatBudgetCell(0, true)).toBe("Not disclosed");
  });

  it("shows the real amount when disclosed", () => {
    expect(formatBudgetCell(50000, false)).toBe("$50,000");
  });
});

describe("formatPercent", () => {
  it("computes a percentage of total", () => {
    expect(formatPercent(1069, 2272)).toBe("47.1%");
  });

  it("returns an em dash for a zero total instead of dividing by zero", () => {
    expect(formatPercent(5, 0)).toBe("—");
  });
});

describe("formatNumber", () => {
  it("adds thousands separators", () => {
    expect(formatNumber(2272)).toBe("2,272");
  });
});
