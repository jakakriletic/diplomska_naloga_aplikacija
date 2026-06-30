import React, { useEffect, useRef, useState } from "react";
import { Send, Bot, User, ExternalLink, Sparkles } from "lucide-react";
import { api } from "../api";
import { Card, Spinner, Badge } from "./ui";

const EXAMPLES = [
  "S čim se ukvarja Etrel?",
  "Kje se lahko vpišem na študij informatike?",
  "Kakšne kontaktne podatke ima organizacija?",
];

function Sources({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Viri
      </p>
      {sources.map((s, i) => (
        <div key={i} className="rounded-lg bg-slate-50 p-2.5 text-xs">
          <div className="mb-1 flex items-center gap-2">
            <span className="font-semibold text-slate-500">[{i + 1}]</span>
            {s.organization && <Badge color="violet">{s.organization}</Badge>}
            {s.url && (
              <a
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 truncate text-indigo-600 hover:underline"
              >
                <ExternalLink className="h-3 w-3 shrink-0" />
                <span className="truncate">{s.url}</span>
              </a>
            )}
          </div>
          <p className="line-clamp-2 text-slate-500">{s.text}</p>
        </div>
      ))}
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]); // {role, content, sources?, error?}
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(question) {
    const text = (question ?? q).trim();
    if (!text || loading) return;
    setQ("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await api.chat(text);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: e.message, error: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e) {
    e.preventDefault();
    send();
  }

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-500" />
          <h2 className="text-lg font-bold text-slate-800">AI klepet</h2>
          <Badge color="amber">bonus</Badge>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Vprašaj v naravnem jeziku. Sistem poišče relevantne odlomke iz zajetih
          podatkov (vektorska baza) in z generativnim modelom sestavi odgovor z
          navedenimi viri <span className="text-slate-400">(RAG)</span>.
        </p>
      </Card>

      {/* Pogovor */}
      <Card className="flex h-[60vh] flex-col p-0">
        <div className="flex-1 space-y-4 overflow-auto p-5">
          {messages.length === 0 && !loading && (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <div className="rounded-2xl bg-indigo-50 p-4 text-indigo-500">
                <Bot className="h-7 w-7" />
              </div>
              <p className="max-w-md text-sm text-slate-400">
                Postavi vprašanje o zajetih organizacijah. Na primer:
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => send(ex)}
                    className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-600"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) =>
            m.role === "user" ? (
              <div key={i} className="flex justify-end gap-2">
                <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-gradient-to-r from-indigo-500 to-violet-500 px-4 py-2.5 text-sm text-white">
                  {m.content}
                </div>
                <div className="mt-1 shrink-0 rounded-full bg-slate-200 p-1.5 text-slate-500">
                  <User className="h-4 w-4" />
                </div>
              </div>
            ) : (
              <div key={i} className="flex gap-2">
                <div className="mt-1 shrink-0 rounded-full bg-indigo-100 p-1.5 text-indigo-600">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="max-w-[80%]">
                  <div
                    className={`rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm ${
                      m.error
                        ? "bg-red-50 text-red-600"
                        : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                    {!m.error && <Sources sources={m.sources} />}
                  </div>
                </div>
              </div>
            )
          )}

          {loading && (
            <div className="flex gap-2">
              <div className="mt-1 shrink-0 rounded-full bg-indigo-100 p-1.5 text-indigo-600">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3 text-sm text-slate-500">
                <Spinner className="h-4 w-4" /> Razmišljam ...
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {/* Vnos */}
        <form onSubmit={onSubmit} className="flex gap-3 border-t border-slate-200 p-4">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Vprašaj kar koli o zajetih podjetjih ..."
            className="flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
          />
          <button
            type="submit"
            disabled={loading || !q.trim()}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-5 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send className="h-4 w-4" /> Pošlji
          </button>
        </form>
      </Card>
    </div>
  );
}
