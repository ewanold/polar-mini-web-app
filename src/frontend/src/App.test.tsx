import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, vi } from "vitest";

import App from "./App";

describe("application shell", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));
  });

  it("redirects the root route to the timeline", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Daily timeline" })).toBeVisible();
    expect(window.location.pathname).toBe("/timeline");
  });

  it("navigates between the initial application areas", async () => {
    window.history.replaceState({}, "", "/timeline");
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("link", { name: "Training" }));
    expect(screen.getByRole("heading", { name: "Training progress" })).toBeVisible();

    await user.click(screen.getByRole("link", { name: "Mappings" }));
    expect(screen.getByRole("heading", { name: "Training mappings" })).toBeVisible();

    await user.click(screen.getByRole("link", { name: "Settings" }));
    expect(screen.getByRole("heading", { name: "Settings and synchronization" })).toBeVisible();
  });

  it("switches theme at runtime and persists the choice", async () => {
    window.history.replaceState({}, "", "/timeline");
    const user = userEvent.setup();
    render(<App />);

    const toggle = screen.getByRole("button", { name: "Switch to dark theme" });
    await user.click(toggle);

    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
    expect(window.localStorage.getItem("polar-theme")).toBe("dark");
    expect(toggle).toHaveAccessibleName("Switch to light theme");
  });

  it("translates navigation, controls, pages, and status text into German", async () => {
    window.history.replaceState({}, "", "/timeline");
    const user = userEvent.setup();
    render(<App />);

    await user.selectOptions(screen.getByLabelText("Language"), "de");
    expect(screen.getByRole("heading", { name: "Tagesverlauf" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Hauptnavigation" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Zum dunklen Design wechseln" })).toHaveTextContent("Dunkel");

    await user.click(screen.getByRole("link", { name: "Training" }));
    expect(screen.getByText("Trainingsanalyse")).toBeVisible();
    expect(screen.getByRole("button", { name: "4 Wochen" })).toBeVisible();
    expect(await screen.findByText("Erstelle unter Zuordnungen eine Trainingsgruppe, um den Fortschritt anzuzeigen.")).toBeVisible();

    await user.click(screen.getByRole("link", { name: "Zuordnungen" }));
    expect(screen.getByLabelText("Gruppenname")).toBeVisible();
    expect(screen.getByRole("button", { name: "Gruppe erstellen" })).toBeVisible();
    expect(await screen.findByText("Noch keine Trainingsgruppen.")).toBeVisible();
    expect(screen.getByText("Noch keine importierten Polar-Trainingseinheiten.")).toBeVisible();

    await user.click(screen.getByRole("link", { name: "Einstellungen" }));
    expect(await screen.findByText("Polar ist nicht verbunden.")).toBeVisible();
    expect(screen.getByRole("link", { name: "Polar verbinden" })).toBeVisible();
  });
});
