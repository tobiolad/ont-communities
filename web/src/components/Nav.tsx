import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Overview", end: true },
  { to: "/map", label: "Map" },
  { to: "/projects", label: "Projects" },
  { to: "/insights", label: "Decision Intelligence" },
];

export function Nav() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div>
          <p className="text-lg font-bold text-ink-primary">Ontario Infrastructure</p>
          <p className="text-xs text-ink-muted">Decision Intelligence Platform</p>
        </div>
        <nav aria-label="Primary" className="flex flex-wrap gap-1">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-brand text-white" : "text-ink-secondary hover:bg-canvas"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
