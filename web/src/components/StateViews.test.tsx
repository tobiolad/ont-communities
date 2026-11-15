import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingState, ErrorState, EmptyState } from "./StateViews";

describe("StateViews", () => {
  it("LoadingState announces itself to assistive tech", () => {
    render(<LoadingState label="Loading projects…" />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading projects…");
  });

  it("ErrorState renders as an alert with the message", () => {
    render(<ErrorState message="Network failure" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Network failure");
  });

  it("EmptyState shows a default message when none is given", () => {
    render(<EmptyState />);
    expect(screen.getByText(/no results match/i)).toBeInTheDocument();
  });

  it("EmptyState shows a custom message", () => {
    render(<EmptyState message="No projects in this region." />);
    expect(screen.getByText("No projects in this region.")).toBeInTheDocument();
  });
});
