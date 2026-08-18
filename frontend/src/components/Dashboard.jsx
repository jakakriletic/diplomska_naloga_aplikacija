import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Globe,
  Eraser,
  Scissors,
  Sparkles,
  Database,
  Boxes,
  Play,
  FileText,
  Building2,
  Layers,
  Hash,
} from "lucide-react";
import { api } from "../api";
import { Card, Button, StatusBadge, Spinner } from "./ui";

const STAGES = [
  { icon: Globe, label: "Zajem", desc: "Web scraping (Scrapy)" },
  { icon: Eraser, label: "Čiščenje", desc: "Normalizacija besedila" },
  { icon: Scissors, label: "Chunking", desc: "Razdelitev na enote" },
  { icon: Sparkles, label: "AI ekstrakcija", desc: "Strukturiranje (OpenAI)" },
  { icon: Database, label: "Relacijska baza", desc: "MySQL" },
  { icon: Boxes, label: "Vektorska baza", desc: "Qdrant" },
];

const RUN_SETTINGS_KEY = "run-settings";
const DEFAULT_RUN_SETTINGS = {
  maxDepth: 2,
  maxPages: 40,
  chunkSize: 1200,
};

function initialRunSettings() {
  if (typeof window === "undefined") return DEFAULT_RUN_SETTINGS;
  try {
    const saved = JSON.parse(window.localStorage.getItem(RUN_SETTINGS_KEY));
    return saved ? { ...DEFAULT_RUN_SETTINGS, ...saved } : DEFAULT_RUN_SETTINGS;
  } catch {
    return DEFAULT_RUN_SETTINGS;
  }
}

function parseIntegerSetting(value, label, min, max) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new Error(`${label} mora biti celo število med ${min} in ${max}.`);
  }
  return parsed;
}

function StatCard({ icon: Icon, label, value, accent }) {
  return (
    <Card className="min-w-0 p-4 sm:p-5">
      <div className="flex min-w-0 items-center gap-3 sm:gap-4">
        <div className={`shrink-0 rounded-xl p-2.5 sm:p-3 ${accent}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="text-2xl font-bold text-slate-800">{value ?? "—"}</p>
          <p className="text-xs leading-tight text-slate-500 sm:text-sm">{label}</p>
        </div>
      </div>
    </Card>
  );
}

export default function Dashboard({ scope }) {
  const [stats, setStats] = useState(null);
  const [run, setRun] = useState(null);
  const [url, setUrl] = useState("");
  const [runSettings, setRunSettings] = useState(initialRunSettings);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const logRef = useRef(null);

  const isActive = run && (run.status === "running" || run.status === "pending");

  const refresh = useCallback(async () => {
    try {
      const [s, latest] = await Promise.all([api.stats(scope), api.latestRun()]);
      setStats(s);
      if (latest) setRun(latest);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, [scope]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Med aktivnim zagonom osvežuj pogosteje
  useEffect(() => {
    const interval = setInterval(refresh, isActive ? 1500 : 8000);
    return () => clearInterval(interval);
  }, [isActive, refresh]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [run?.log]);

  async function startRun() {
    let parsedSettings;
    try {
      parsedSettings = {
        maxDepth: parseIntegerSetting(runSettings.maxDepth, "Globina zajema", 0, 5),
        maxPages: parseIntegerSetting(runSettings.maxPages, "Omejitev strani", 1, 200),
        chunkSize: parseIntegerSetting(runSettings.chunkSize, "Velikost odseka", 300, 4000),
      };
    } catch (e) {
      setError(e.message);
      return;
    }

    setStarting(true);
    setError(null);
    try {
      const r = await api.runPipeline(url.trim(), parsedSettings);
      setRun(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setStarting(false);
    }
  }

  function updateRunSetting(name, value) {
    const next = { ...runSettings, [name]: value };
    setRunSettings(next);
    window.localStorage.setItem(RUN_SETTINGS_KEY, JSON.stringify(next));
  }

  return (
    <div className="space-y-6">
      {/* Statistika */}
      <div className="grid grid-cols-1 gap-4 min-[360px]:grid-cols-2 lg:grid-cols-5">
        <StatCard icon={Play} label="Zagoni" value={stats?.runs} accent="bg-indigo-100 text-indigo-600" />
        <StatCard icon={Building2} label="Organizacije" value={stats?.organizations} accent="bg-violet-100 text-violet-600" />
        <StatCard icon={FileText} label="Strani" value={stats?.pages} accent="bg-blue-100 text-blue-600" />
        <StatCard icon={Layers} label="Chunki" value={stats?.chunks} accent="bg-emerald-100 text-emerald-600" />
        <StatCard icon={Hash} label="Vektorji" value={stats?.vectors} accent="bg-amber-100 text-amber-600" />
      </div>

      {/* Zagon pipelina */}
      <Card className="p-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-lg font-bold text-slate-800">Zaženi obdelavo</h2>
          <p className="text-sm text-slate-500">
            Vnesi spletni naslov za zajem. Če pustiš prazno, se uporabi privzeti
            testni vir (FEI UNM).
          </p>
        </div>

        <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-4">
          <div className="mb-3">
            <h3 className="text-sm font-bold text-slate-700">Nastavitve naslednjega zajema</h3>
            <p className="text-xs text-slate-400">
              Nastavitve veljajo samo za novi zagon in ne spreminjajo že shranjenih podatkov.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="min-w-0 text-xs font-semibold text-slate-500">
              Globina zajema
              <input
                type="number"
                min="0"
                max="5"
                step="1"
                value={runSettings.maxDepth}
                disabled={isActive}
                onChange={(e) => updateRunSetting("maxDepth", e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 disabled:opacity-60"
              />
              <span className="mt-1 block font-normal text-slate-400">0–5 ravni povezav</span>
            </label>
            <label className="min-w-0 text-xs font-semibold text-slate-500">
              Omejitev strani
              <input
                type="number"
                min="1"
                max="200"
                step="1"
                value={runSettings.maxPages}
                disabled={isActive}
                onChange={(e) => updateRunSetting("maxPages", e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 disabled:opacity-60"
              />
              <span className="mt-1 block font-normal text-slate-400">največ 1–200 strani</span>
            </label>
            <label className="min-w-0 text-xs font-semibold text-slate-500">
              Velikost odseka
              <input
                type="number"
                min="300"
                max="4000"
                step="100"
                value={runSettings.chunkSize}
                disabled={isActive}
                onChange={(e) => updateRunSetting("chunkSize", e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 disabled:opacity-60"
              />
              <span className="mt-1 block font-normal text-slate-400">300–4000 znakov</span>
            </label>
          </div>
        </div>
        <div className="mt-4 flex min-w-0 flex-col gap-3 sm:flex-row">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://fei.uni-nm.si/"
            className="flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          />
          <Button onClick={startRun} disabled={starting || isActive}>
            {starting || isActive ? <Spinner className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isActive ? "Obdelava poteka ..." : "Zaženi zajem"}
          </Button>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </Card>

      {/* Koraki pipelina */}
      <Card className="p-6">
        <h2 className="mb-5 text-lg font-bold text-slate-800">Potek pipelina</h2>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch">
          {STAGES.map((stage, i) => (
            <React.Fragment key={stage.label}>
              <div
                className={`flex min-w-0 flex-1 items-center gap-3 rounded-xl border p-3 transition ${
                  isActive
                    ? "border-indigo-200 bg-indigo-50/50"
                    : "border-slate-100 bg-slate-50"
                }`}
              >
                <div className="rounded-lg bg-white p-2 text-indigo-600 shadow-sm">
                  <stage.icon className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-700">{stage.label}</p>
                  <p className="truncate text-xs text-slate-400">{stage.desc}</p>
                </div>
              </div>
              {i < STAGES.length - 1 && (
                <div className="hidden items-center text-slate-300 lg:flex">→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </Card>

      {/* Status zadnjega zagona + dnevnik */}
      {run && (
        <Card className="p-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-slate-800">Zadnji zagon</h2>
              <StatusBadge status={run.status} />
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-slate-500">
              <span>Strani: <b className="text-slate-700">{run.pages_scraped}</b></span>
              <span>Chunki: <b className="text-slate-700">{run.chunks_created}</b></span>
              <span>Organizacije: <b className="text-slate-700">{run.organizations_extracted}</b></span>
            </div>
          </div>
          <p className="mb-3 truncate text-sm text-slate-500">
            Vir: <span className="font-medium text-slate-700">{run.source_url}</span>
          </p>
          {run.error && (
            <p className="mb-3 rounded-lg bg-red-50 p-3 text-sm text-red-600">{run.error}</p>
          )}
          <div
            ref={logRef}
            className="max-h-72 overflow-auto rounded-xl bg-slate-900 p-4 font-mono text-xs leading-relaxed text-slate-300"
          >
            {run.log ? (
              run.log.split("\n").map((line, i) => <div key={i}>{line}</div>)
            ) : (
              <span className="text-slate-500">Dnevnik je prazen ...</span>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
