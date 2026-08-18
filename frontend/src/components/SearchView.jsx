import React, { useState } from "react";
import { Search, Sparkles, Type, ExternalLink } from "lucide-react";
import { api } from "../api";
import { Card, Spinner, Empty, Badge } from "./ui";

function ScoreBar({ score }) {
  const pct = Math.max(0, Math.min(100, Math.round(score * 100)));
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-500">{pct}%</span>
    </div>
  );
}

function Highlight({ text, q }) {
  if (!q) return <>{text}</>;
  const parts = text.split(new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig"));
  return (
    <>
      {parts.map((p, i) =>
        p.toLowerCase() === q.toLowerCase() ? (
          <mark key={i} className="rounded bg-amber-200/70 px-0.5">{p}</mark>
        ) : (
          <React.Fragment key={i}>{p}</React.Fragment>
        )
      )}
    </>
  );
}

export default function SearchView({ scope }) {
  const [mode, setMode] = useState("semantic"); // 'semantic' | 'keyword'
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  function changeMode(nextMode) {
    setMode(nextMode);
    setResults([]);
    setError(null);
    setSearched(false);
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data =
        mode === "semantic"
          ? await api.semantic(q.trim(), 10, scope)
          : await api.keyword(q.trim(), 20, scope);
      setResults(data);
    } catch (e) {
      setError(e.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-lg font-bold text-slate-800">Iskanje po vsebini</h2>
        <p className="mb-4 text-sm text-slate-500">
          Primerjaj <b>semantično</b> iskanje (po pomenu, vektorska baza Qdrant) z
          <b> klasičnim</b> iskanjem po ključnih besedah (relacijska baza MySQL).
        </p>

        {/* Preklop načina */}
        <div className="mb-4 flex w-full flex-col rounded-xl bg-slate-100 p-1 sm:w-auto sm:flex-row">
          <button
            onClick={() => changeMode("semantic")}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
              mode === "semantic" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500"
            }`}
          >
            <Sparkles className="h-4 w-4" /> Semantično (Qdrant)
          </button>
          <button
            onClick={() => changeMode("keyword")}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
              mode === "keyword" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500"
            }`}
          >
            <Type className="h-4 w-4" /> Ključne besede (MySQL)
          </button>
        </div>

        <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={
                mode === "semantic"
                  ? "Npr.: kje se lahko vpišem na študij informatike?"
                  : "Npr.: informatika"
              }
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <button
            type="submit"
            className="rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-5 text-sm font-semibold text-white"
          >
            Išči
          </button>
        </form>
      </Card>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-indigo-500" />
        </div>
      ) : error ? (
        <Card className="p-4">
          <p className="text-sm text-red-600">{error}</p>
        </Card>
      ) : searched && results.length === 0 ? (
        <Empty icon={Search} title="Ni zadetkov" hint="Poskusi z drugačno poizvedbo." />
      ) : (
        <div className="space-y-3">
          {results.map((hit, i) => (
            <Card key={i} className="p-5">
              <div className="mb-2 flex items-center justify-between gap-3">
                <a
                  href={hit.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 truncate text-sm font-medium text-indigo-600 hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{hit.url}</span>
                </a>
                {mode === "semantic" ? (
                  <ScoreBar score={hit.score} />
                ) : (
                  <Badge color="blue">ujemanje besede</Badge>
                )}
              </div>
              {mode === "semantic" && hit.organization && (
                <Badge color="violet">{hit.organization}</Badge>
              )}
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                <Highlight text={hit.text} q={mode === "keyword" ? q : ""} />
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
