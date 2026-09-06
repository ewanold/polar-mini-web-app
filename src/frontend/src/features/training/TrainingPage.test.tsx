import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageProvider } from "../../i18n/LanguageProvider";
import { TrainingPage } from "./TrainingPage";

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<LanguageProvider><QueryClientProvider client={queryClient}><BrowserRouter><TrainingPage /></BrowserRouter></QueryClientProvider></LanguageProvider>);
}

describe("TrainingPage", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] })));

  it("shows the three progress ranges and an empty setup state", async () => {
    renderPage();
    expect(await screen.findByRole("button", { name: "4 weeks" })).toBeVisible();
    expect(screen.getByRole("button", { name: "6 months" })).toBeVisible();
    expect(screen.getByRole("button", { name: "All" })).toBeVisible();
    expect(await screen.findByText("Create a training group in Mappings to view progress.")).toBeVisible();
  });

  it("restores group and range selection from the URL", async () => {
    window.history.replaceState({}, "", "/training?range=6m&group=2");
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: true, json: async () => [{ id: 1, name: "Running", color: "#006f7b" }, { id: 2, name: "Walking", color: "#216869" }] } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ buckets: [] }) } as Response);
    renderPage();
    expect(await screen.findByText("No mapped training sessions in this range.")).toBeVisible();
    expect(screen.getByLabelText("Training group")).toHaveValue("2");
    expect(screen.getByRole("button", { name: "6 months" })).toHaveAttribute("aria-pressed", "true");
    expect(fetch).toHaveBeenLastCalledWith("/api/training/groups/2/series?range=6m");
  });

  it("writes range changes to the URL", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({ ok: true, json: async () => [{ id: 1, name: "Running", color: "#006f7b" }] } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ buckets: [] }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ buckets: [] }) } as Response);
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "All" }));
    expect(window.location.search).toBe("?range=all&group=1");
  });
});
