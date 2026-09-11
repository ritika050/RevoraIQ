import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import AdminPage from "./pages/AdminPage";
import AuditPage from "./pages/AuditPage";
import Dashboard from "./pages/Dashboard";
import EventDetailPage from "./pages/EventDetailPage";
import SearchPage from "./pages/SearchPage";
import { connectStream } from "./services/api";

export default function App() {
  const [live, setLive] = useState(false);
  const [pipeline, setPipeline] = useState({
    stage: "",
    message: "",
    demoMessage: "",
    tick: 0,
  });

  useEffect(() => {
    const source = connectStream((type, payload) => {
      if (type === "ready") setLive(true);
      if (type === "pipeline") {
        setPipeline((prev) => ({
          ...prev,
          stage: payload.stage || prev.stage,
          message: payload.message || prev.message,
          tick: prev.tick + 1,
        }));
      }
      if (type === "demo") {
        setPipeline((prev) => ({ ...prev, demoMessage: payload.message, tick: prev.tick + 1 }));
      }
      if (["event", "alert", "metrics", "action"].includes(type)) {
        setPipeline((prev) => ({ ...prev, tick: prev.tick + 1 }));
      }
    });
    source.onerror = () => setLive(false);
    return () => source.close();
  }, []);

  return (
    <Routes>
      <Route element={<Layout live={live} pipelineStage={pipeline.message} />}>
        <Route path="/" element={<Dashboard pipeline={pipeline} />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/events/:eventId" element={<EventDetailPage />} />
      </Route>
    </Routes>
  );
}
