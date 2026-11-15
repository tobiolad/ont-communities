import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, StatusBadge } from "./Badge";

describe("Badge", () => {
  it("renders the given label", () => {
    render(<Badge label="Infrastructure" />);
    expect(screen.getByText("Infrastructure")).toBeInTheDocument();
  });
});

describe("StatusBadge", () => {
  it("renders a known status", () => {
    render(<StatusBadge status="Complete" />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("renders gracefully for an unexpected status instead of crashing", () => {
    render(<StatusBadge status="Something New" />);
    expect(screen.getByText("Something New")).toBeInTheDocument();
  });
});
