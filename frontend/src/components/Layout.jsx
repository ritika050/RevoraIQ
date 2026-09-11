import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Intelligence" },
  { to: "/search", label: "Search & Analysis" },
  { to: "/audit", label: "Audit Logs" },
  { to: "/admin", label: "Admin / Ops" },
];

export default function Layout({ live, pipelineStage }) {
  return (
    <div className="min-h-screen">
      <div className="flex">
        <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-white/10 bg-ink-900/90 p-5 lg:block">
          <div className="mb-8">
            <div className="text-xl font-semibold tracking-tight text-white">RevoralQ</div>
            <div className="mt-1 text-xs leading-relaxed text-slate-400">Real-Time AI Monitoring & Intelligence</div>
          </div>
          <nav className="space-y-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `block rounded-xl px-3 py-2 text-sm ${
                    isActive ? "bg-accent/15 text-accent" : "text-slate-300 hover:bg-white/5"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-10 rounded-xl border border-white/10 p-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${live ? "bg-emerald-400" : "bg-rose-400"}`} />
              {live ? "Live stream connected" : "Connecting stream..."}
            </div>
            <div className="mt-2 text-slate-500">{pipelineStage || "Processor idle"}</div>
          </div>
        </aside>
        <main className="min-h-screen flex-1 p-4 lg:p-8">
          <header className="mb-6 flex flex-col gap-3 border-b border-white/10 pb-4 lg:hidden">
            <div>
              <div className="text-lg font-semibold">RevoralQ</div>
              <div className="text-xs text-slate-400">Real-Time AI Monitoring & Intelligence</div>
            </div>
            <div className="flex flex-wrap gap-2">
              {links.map((link) => (
                <NavLink key={link.to} to={link.to} className="btn-ghost text-xs">
                  {link.label}
                </NavLink>
              ))}
            </div>
          </header>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
