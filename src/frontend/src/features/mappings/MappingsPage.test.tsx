import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageProvider } from "../../i18n/LanguageProvider";
import { MappingsPage } from "./MappingsPage";

function renderPage() {
  return render(<LanguageProvider><MappingsPage /></LanguageProvider>);
}

describe("MappingsPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));
  });

  it("creates a training group", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => [] } as Response).mockResolvedValueOnce({ ok: true, json: async () => [] } as Response).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 1, name: "Running", slug: "running", color: "#006f7b", position: 0, enabled: true }),
    } as Response);
    const user = userEvent.setup();
    renderPage();

    await user.type(await screen.findByLabelText("Group name"), "Running");
    await user.click(screen.getByRole("button", { name: "Create group" }));

    expect(fetch).toHaveBeenLastCalledWith("/api/training/groups", expect.objectContaining({ method: "POST" }));
    expect(await screen.findByText("Running")).toBeVisible();
  });

  it("lists observed sport types and updates an assignment", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: 1, name: "Running", slug: "running", color: "#006f7b", position: 0, enabled: true }],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ sport_type: "RUNNING", session_count: 3, state: "unmapped", group_id: null }],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sport_type: "RUNNING", session_count: 3, state: "mapped", group_id: 1 }),
      } as Response);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("RUNNING")).toBeVisible();
    expect(screen.getByText("3 sessions are not assigned to a training group.")).toBeVisible();
    await user.selectOptions(screen.getByLabelText("Assign RUNNING"), "group:1");

    expect(fetch).toHaveBeenLastCalledWith(
      "/api/training/sport-types/RUNNING",
      expect.objectContaining({ method: "PUT", body: JSON.stringify({ state: "mapped", group_id: 1 }) }),
    );
    expect(screen.getByLabelText("Assign RUNNING")).toHaveValue("group:1");
  });

  it("confirms unmapping before deleting a training group", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: 1, name: "Running", slug: "running", color: "#006f7b", position: 0, enabled: true }],
      } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => [] } as Response)
      .mockResolvedValueOnce({ ok: true } as Response);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Delete Running" }));
    expect(screen.getByRole("dialog", { name: "Delete Running?" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Unmap and delete" }));

    expect(fetch).toHaveBeenLastCalledWith(
      "/api/training/groups/1",
      expect.objectContaining({
        method: "DELETE",
        body: JSON.stringify({ disposition: "unmapped" }),
      }),
    );
    expect(screen.queryByText("Running")).not.toBeInTheDocument();
  });

  it("can reassign mapped sport types before deleting a training group", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { id: 1, name: "Running", slug: "running", color: "#006f7b", position: 0, enabled: true },
          { id: 2, name: "Walking", slug: "walking", color: "#216869", position: 1, enabled: true },
        ],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ sport_type: "RUNNING", session_count: 3, state: "mapped", group_id: 1 }],
      } as Response)
      .mockResolvedValueOnce({ ok: true } as Response);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Delete Running" }));
    expect(screen.getByLabelText("Reassign mapped types to")).toHaveValue("2");
    await user.click(screen.getByRole("button", { name: "Reassign and delete" }));

    expect(fetch).toHaveBeenLastCalledWith(
      "/api/training/groups/1",
      expect.objectContaining({
        method: "DELETE",
        body: JSON.stringify({ disposition: "reassign", replacement_group_id: 2 }),
      }),
    );
    expect(screen.getByLabelText("Assign RUNNING")).toHaveValue("group:2");
  });
});
