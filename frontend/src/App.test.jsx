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
  window.localStorage.clear();
  api.stats.mockResolvedValue(stats);
  const latestRun = {
    id: "run-1",
    status: "partial",
    source_url: "https://example.com/",
    pages_scraped: 1,
    chunks_created: 1,
    organizations_extracted: 0,
    error: null,
    log: "Prva vrstica\nPipeline zaključen z opozorili (1).",
  };
  api.latestRun.mockResolvedValue(latestRun);
  api.runPipeline.mockResolvedValue(latestRun);
  api.organizations.mockResolvedValue([]);
  api.pages.mockImplementation((_limit, offset, _scope) =>
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
    expect(api.organizations).toHaveBeenCalledWith("", "latest");
  });

  it("preklopi na naslednjo stran zajetih strani", async () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole("button", { name: "Zajete strani" })[0]);
    expect(await screen.findByText("https://example.com/prva")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Naslednja/ }));

    await waitFor(() => expect(api.pages).toHaveBeenCalledWith(50, 50, "latest"));
    expect(await screen.findByText("https://example.com/druga")).toBeInTheDocument();
  });

  it("globalno preklopi na celotno zgodovino in izbiro shrani", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Vsi podatki" }));

    await waitFor(() => expect(api.stats).toHaveBeenCalledWith("all"));
    expect(window.localStorage.getItem("data-scope")).toBe("all");

    fireEvent.click(screen.getAllByRole("button", { name: "Organizacije" })[0]);
    await waitFor(() => expect(api.organizations).toHaveBeenCalledWith("", "all"));
  });

  it("pošlje nastavitve naslednjega zajema", async () => {
    render(<App />);

    fireEvent.change(screen.getByRole("spinbutton", { name: /Globina zajema/ }), {
      target: { value: "3" },
    });
    fireEvent.change(screen.getByRole("spinbutton", { name: /Omejitev strani/ }), {
      target: { value: "75" },
    });
    fireEvent.change(screen.getByRole("spinbutton", { name: /Velikost odseka/ }), {
      target: { value: "900" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Zaženi zajem" }));

    await waitFor(() =>
      expect(api.runPipeline).toHaveBeenCalledWith("", {
        maxDepth: 3,
        maxPages: 75,
        chunkSize: 900,
      }),
    );
  });
});
