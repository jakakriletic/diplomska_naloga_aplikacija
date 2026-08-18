import React, { useState } from "react";
import {
  LayoutDashboard,
  Building2,
  Search,
  FileText,
  Boxes,
  MessageSquare,
} from "lucide-react";
import Dashboard from "./components/Dashboard.jsx";
import Organizations from "./components/Organizations.jsx";
import SearchView from "./components/SearchView.jsx";
import Pages from "./components/Pages.jsx";
import Chat from "./components/Chat.jsx";

const NAV = [
  { id: "dashboard", label: "Nadzorna plošča", icon: LayoutDashboard, component: Dashboard },
  { id: "organizations", label: "Organizacije", icon: Building2, component: Organizations },
  { id: "search", label: "Iskanje", icon: Search, component: SearchView },
  { id: "chat", label: "AI klepet", icon: MessageSquare, component: Chat },
  { id: "pages", label: "Zajete strani", icon: FileText, component: Pages },
];

const DATA_SCOPE_KEY = "data-scope";

function initialDataScope() {
  if (typeof window === "undefined") return "latest";
  return window.localStorage.getItem(DATA_SCOPE_KEY) === "all" ? "all" : "latest";
}

function ScopeToggle({ scope, onChange }) {
  return (
    <div className="flex items-center justify-between gap-2 sm:justify-end">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Obseg podatkov
      </span>
      <div
        className="inline-flex rounded-xl bg-slate-100 p-1"
        role="group"
        aria-label="Obseg podatkov"
      >
        <button
          type="button"
          aria-pressed={scope === "latest"}
          onClick={() => onChange("latest")}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition sm:text-sm ${
            scope === "latest"
              ? "bg-white text-indigo-600 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
          title="Uporabi zadnji uspešni zajem vsake domene"
        >
          Najnovejši
        </button>
        <button
          type="button"
          aria-pressed={scope === "all"}
          onClick={() => onChange("all")}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition sm:text-sm ${
            scope === "all"
              ? "bg-white text-indigo-600 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
          title="Uporabi podatke vseh preteklih zajemov"
        >
          Vsi podatki
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState("dashboard");
  const [scope, setScope] = useState(initialDataScope);
  const Current = NAV.find((n) => n.id === active)?.component ?? Dashboard;
  const activeLabel = NAV.find((n) => n.id === active)?.label;

  function changeScope(nextScope) {
    setScope(nextScope);
    window.localStorage.setItem(DATA_SCOPE_KEY, nextScope);
  }

  return (
    <div className="flex min-h-screen">
      {/* Stranska vrstica */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white p-5 lg:flex">
        <div className="mb-8 flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 p-2.5 text-white">
            <Boxes className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-bold leading-tight text-slate-800">Zajem podatkov</p>
            <p className="text-xs text-slate-400">z generativno UI</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                active === item.id
                  ? "bg-indigo-50 text-indigo-600"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="mt-auto rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-400">
          Diplomski prototip — modularni sistem za zajem, strukturiranje in
          shranjevanje podatkov o podjetjih.
        </div>
      </aside>

      {/* Glavna vsebina */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Glava */}
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 px-4 py-4 backdrop-blur sm:px-6">
          <div className="flex min-w-0 flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex min-w-0 items-center justify-between gap-2">
            <div>
              <h1 className="text-lg font-bold text-slate-800 sm:text-xl">{activeLabel}</h1>
            </div>
            {/* Mobilna navigacija */}
            <nav className="flex shrink-0 gap-0.5 lg:hidden">
              {NAV.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActive(item.id)}
                  className={`rounded-lg p-1.5 sm:p-2 ${
                    active === item.id ? "bg-indigo-50 text-indigo-600" : "text-slate-500"
                  }`}
                  title={item.label}
                >
                  <item.icon className="h-5 w-5" />
                </button>
              ))}
            </nav>
            </div>
            <ScopeToggle scope={scope} onChange={changeScope} />
          </div>
        </header>

        <main className="mx-auto min-w-0 w-full max-w-6xl flex-1 p-4 sm:p-6">
          <Current key={`${active}-${scope}`} scope={scope} />
        </main>
      </div>
    </div>
  );
}
