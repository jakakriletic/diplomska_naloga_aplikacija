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

export default function App() {
  const [active, setActive] = useState("dashboard");
  const Current = NAV.find((n) => n.id === active)?.component ?? Dashboard;
  const activeLabel = NAV.find((n) => n.id === active)?.label;

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
      <div className="flex flex-1 flex-col">
        {/* Glava */}
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-800">{activeLabel}</h1>
            </div>
            {/* Mobilna navigacija */}
            <nav className="flex gap-1 lg:hidden">
              {NAV.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActive(item.id)}
                  className={`rounded-lg p-2 ${
                    active === item.id ? "bg-indigo-50 text-indigo-600" : "text-slate-500"
                  }`}
                  title={item.label}
                >
                  <item.icon className="h-5 w-5" />
                </button>
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 p-6">
          <Current />
        </main>
      </div>
    </div>
  );
}
