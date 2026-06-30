// Tanek sloj za klice na backend REST API.
// V produkciji nginx preusmeri /api -> backend; med razvojem to stori Vite.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Pipeline
  runPipeline: (url) =>
    request("/api/pipeline/run", {
      method: "POST",
      body: JSON.stringify({ url: url || null }),
    }),
  latestRun: () => request("/api/pipeline/latest"),
  getRun: (id) => request(`/api/pipeline/runs/${id}`),
  listRuns: () => request("/api/pipeline/runs"),

  // Statistika
  stats: () => request("/api/stats"),

  // Organizacije
  organizations: (q) =>
    request(`/api/organizations${q ? `?q=${encodeURIComponent(q)}` : ""}`),

  // Strani
  pages: () => request("/api/pages"),
  page: (id) => request(`/api/pages/${id}`),
  pageChunks: (id) => request(`/api/pages/${id}/chunks`),

  // Iskanje
  semantic: (q, limit = 10) =>
    request(`/api/search/semantic?q=${encodeURIComponent(q)}&limit=${limit}`),
  keyword: (q, limit = 20) =>
    request(`/api/search/keyword?q=${encodeURIComponent(q)}&limit=${limit}`),

  // AI klepet (RAG) — bonus
  chat: (question, limit = 6) =>
    request("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question, limit }),
    }),
};
