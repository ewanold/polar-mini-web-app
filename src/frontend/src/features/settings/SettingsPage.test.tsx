import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";

import { LanguageProvider } from "../../i18n/LanguageProvider";
import { SettingsPage } from "./SettingsPage";

function renderPage() {
  return render(<LanguageProvider><SettingsPage /></LanguageProvider>);
}

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ connected: false, polar_user_id: null, expires_at: null }),
      }),
    );
  });

  it("shows the Polar connection state and a connect action", async () => {
    renderPage();

    expect(await screen.findByText("Polar is not connected.")).toBeVisible();
    expect(screen.getByRole("link", { name: "Connect Polar" })).toHaveAttribute(
      "href",
      "/api/polar/connect",
    );
  });

  it("shows the last successful synchronization when status provides it", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        connected: true,
        polar_user_id: "62661976",
        expires_at: null,
        last_success_at: "2026-09-06T10:15:00+00:00",
      }),
    } as Response);

    renderPage();

    expect(await screen.findByText(/Last successful sync:/)).toBeVisible();
  });

  it("runs a Polar synchronization and displays every category outcome", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ connected: true, polar_user_id: "62661976", expires_at: null }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          connected: true,
          categories: { activity: { inserted: 0, updated: 0, skipped: 28, errors: 0 } },
        }),
      } as Response);
    const user = userEvent.setup();

    renderPage();
    await user.click(await screen.findByRole("button", { name: "Sync now" }));

    expect(fetch).toHaveBeenLastCalledWith("/api/polar/sync", { method: "POST" });
    expect(await screen.findByText("Synchronization completed.")).toBeVisible();
    expect(screen.getByText("Activity: 0 new, 0 updated, 28 unchanged, 0 errors")).toBeVisible();
  });
});
