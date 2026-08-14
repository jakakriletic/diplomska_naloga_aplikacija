import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App.jsx";
import { api } from "./api";

vi.mock("./api", () => ({
  api: {
    runPipeline: vi.fn(),
    latestRun: vi.fn(),
    getRun: vi.fn(),
    listRuns: vi.fn(),
    stats: vi.fn(),
    organizations: vi.fn(),
    pages: vi.fn(),
    page: vi.fn(),
    pageChunks: vi.fn(),
    semantic: vi.fn(),
    keyword: vi.fn(),
    chat: vi.fn(),
  },
}));

const stats = {
  runs: 2,
  organizations: 1,
  pages: 51,
  chunks: 4,
  vectors: 4,
  last_run: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  api.stats.mockResolvedValue(stats);
  api.latestRun.mockResolvedValue({
    id: "run-1",
    status: "partial",
    source_url: "https://example.com/",
    pages_scraped: 1,
    chunks_created: 1,
    organizations_extracted: 0,
    error: null,
    log: "Prva vrstica\nPipeline zaključen z opozorili (1).",
  });
  api.organizations.mockResolvedValue([]);
  api.pages.mockImplementation((_limit, offset) =>
    Promise.resolve([
      {
        id: offset === 0 ? 1 : 2,
        run_id: "run-1",
        url: offset === 0 ? "https://example.com/prva" : "https://example.com/druga",
        depth: 0,
        char_count: 100,
      },
    ]),
  );
});

describe("App", () => {
  it("prikaže delni status in dnevnik zadnjega zagona", async () => {
    render(<App />);

    expect(await screen.findByText("Zaključeno z opozorili")).toBeInTheDocument();
    expect(screen.getByText("Prva vrstica")).toBeInTheDocument();
  });

  it("odpre seznam organizacij", async () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole("button", { name: "Organizacije" })[0]);

    expect(await screen.findByText("Ni organizacij")).toBeInTheDocument();
    expect(api.organizations).toHaveBeenCalledWith("");
  });

  it("preklopi na naslednjo stran zajetih strani", async () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole("button", { name: "Zajete strani" })[0]);
    expect(await screen.findByText("https://example.com/prva")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Naslednja/ }));

    await waitFor(() => expect(api.pages).toHaveBeenCalledWith(50, 50));
    expect(await screen.findByText("https://example.com/druga")).toBeInTheDocument();
  });
});
