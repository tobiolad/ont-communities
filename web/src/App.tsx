import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { Nav } from "./components/Nav";
import { LoadingState } from "./components/StateViews";

const OverviewPage = lazy(() => import("./pages/OverviewPage").then((m) => ({ default: m.OverviewPage })));
const MapPage = lazy(() => import("./pages/MapPage").then((m) => ({ default: m.MapPage })));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage").then((m) => ({ default: m.ProjectsPage })));
const ProjectDetailPage = lazy(() => import("./pages/ProjectDetailPage").then((m) => ({ default: m.ProjectDetailPage })));
const InsightsPage = lazy(() => import("./pages/InsightsPage").then((m) => ({ default: m.InsightsPage })));

export default function App() {
  return (
    <div className="min-h-screen bg-canvas">
      <Nav />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <Suspense fallback={<LoadingState label="Loading page…" />}>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />
            <Route path="/insights" element={<InsightsPage />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="mx-auto max-w-7xl px-4 py-8 text-xs text-ink-muted sm:px-6">
        Data: Ontario Builds: Communities, Ontario Data Catalogue (Open Government Licence – Ontario). This
        is an independent analysis, not an official Government of Ontario product.
      </footer>
    </div>
  );
}
