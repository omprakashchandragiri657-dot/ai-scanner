import { Navigate, Route, Routes } from "react-router-dom";
import FindingDetail from "./components/FindingDetail";
import Sidebar from "./components/Sidebar";
import { useScan } from "./context/ScanContext";
import Dashboard from "./pages/Dashboard";
import Findings from "./pages/Findings";
import ProjectScanner from "./pages/ProjectScanner";
import Research from "./pages/Research";
import About from "./pages/About";

export default function App() {
  const { selectedFinding, selectFinding } = useScan();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-200">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scanner" element={<ProjectScanner />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/research" element={<Research />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      {selectedFinding && (
        <FindingDetail
          finding={selectedFinding}
          onClose={() => selectFinding(null)}
        />
      )}
    </div>
  );
}
