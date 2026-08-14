import React, { useEffect, useState } from "react";
import {
  FileText,
  ExternalLink,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { api } from "../api";
import { Card, Badge, Button, Spinner, Empty } from "./ui";

const PAGE_SIZE = 50;

function PageDetail({ pageId, onBack }) {
  const [tab, setTab] = useState("text"); // 'text' | 'chunks'
  const [page, setPage] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [p, c] = await Promise.all([api.page(pageId), api.pageChunks(pageId)]);
        if (!cancelled) {
          setPage(p);
          setChunks(c);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [pageId]);

  if (loading)
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-indigo-500" />
      </div>
    );
  if (error)
    return (
      <div className="space-y-4">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-indigo-600"
        >
          <ArrowLeft className="h-4 w-4" /> Nazaj na seznam
        </button>
        <Card className="p-4">
          <p className="text-sm text-red-600">{error}</p>
        </Card>
      </div>
    );
  if (!page) return null;

  return (
    <div className="space-y-4">
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-indigo-600"
      >
        <ArrowLeft className="h-4 w-4" /> Nazaj na seznam
      </button>

      <Card className="p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <a
            href={page.url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 break-all text-sm font-semibold text-indigo-600 hover:underline"
          >
            <ExternalLink className="h-4 w-4 shrink-0" /> {page.url}
          </a>
          <div className="flex gap-2">
            <Badge color="slate">globina {page.depth}</Badge>
            <Badge color="blue">{page.char_count} znakov</Badge>
            <Badge color="emerald">{chunks.length} chunkov</Badge>
          </div>
        </div>

        <div className="mb-4 inline-flex rounded-xl bg-slate-100 p-1">
          <button
            onClick={() => setTab("text")}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              tab === "text" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500"
            }`}
          >
            Očiščeno besedilo
          </button>
          <button
            onClick={() => setTab("chunks")}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
              tab === "chunks" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500"
            }`}
          >
            Chunki ({chunks.length})
          </button>
        </div>

        {tab === "text" ? (
          <p className="whitespace-pre-wrap rounded-xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-600">
            {page.clean_text}
          </p>
        ) : (
          <div className="space-y-3">
            {chunks.map((c) => (
              <div key={c.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="mb-1 flex items-center gap-2">
                  <Badge color="violet">#{c.chunk_index}</Badge>
                  <span className="text-xs text-slate-400">{c.char_count} znakov</span>
                </div>
                <p className="text-sm leading-relaxed text-slate-600">{c.text}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default function Pages() {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [items, stats] = await Promise.all([
          api.pages(PAGE_SIZE, offset),
          api.stats(),
        ]);
        if (!cancelled) {
          setPages(items);
          setTotal(stats.pages);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [offset]);

  if (selected) return <PageDetail pageId={selected} onBack={() => setSelected(null)} />;

  if (loading)
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-6 w-6 text-indigo-500" />
      </div>
    );

  if (error)
    return (
      <Card className="p-4">
        <p className="text-sm text-red-600">{error}</p>
      </Card>
    );

  if (pages.length === 0)
    return (
      <Empty
        icon={FileText}
        title="Ni zajetih strani"
        hint="Zaženi obdelavo na nadzorni plošči."
      />
    );

  return (
    <div className="space-y-3">
      <Card className="p-5">
        <h2 className="text-lg font-bold text-slate-800">Zajete strani</h2>
        <p className="text-sm text-slate-500">
          Spletne strani, ki jih je zajel in očistil modul za web scraping. Klikni za podrobnosti in chunke.
        </p>
        <p className="mt-2 text-xs font-medium text-slate-400">
          Prikaz {offset + 1}–{Math.min(offset + pages.length, total)} od {total}
        </p>
      </Card>
      {pages.map((p) => (
        <Card
          key={p.id}
          className="transition hover:border-indigo-200 hover:shadow-md"
        >
          <button
            type="button"
            onClick={() => setSelected(p.id)}
            className="flex w-full min-w-0 items-center justify-between gap-4 p-4 text-left"
          >
            <div className="flex min-w-0 items-center gap-3">
              <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
                <FileText className="h-4 w-4" />
              </div>
              <span className="truncate text-sm font-medium text-slate-700">{p.url}</span>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Badge color="slate">globina {p.depth}</Badge>
              <Badge color="blue">{p.char_count} z.</Badge>
            </div>
          </button>
        </Card>
      ))}

      {total > PAGE_SIZE && (
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <Button
            variant="ghost"
            disabled={offset === 0}
            onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
          >
            <ChevronLeft className="h-4 w-4" /> Prejšnja
          </Button>
          <span className="text-sm font-medium text-slate-500">
            Stran {Math.floor(offset / PAGE_SIZE) + 1} od {Math.ceil(total / PAGE_SIZE)}
          </span>
          <Button
            variant="ghost"
            disabled={offset + PAGE_SIZE >= total}
            onClick={() => setOffset((value) => value + PAGE_SIZE)}
          >
            Naslednja <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
