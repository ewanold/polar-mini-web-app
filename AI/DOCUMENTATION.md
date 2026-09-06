# Documentation Guide

## Purpose

The Markdown files in this directory are the durable source of project knowledge. The project should remain understandable and resumable from these files without requiring access to a previous chat transcript.

## Maintenance Rule

When the user asks to update, refresh, or synchronize the project documentation:

1. Review every visible Markdown file in this directory, not only the file most closely related to the latest change.
2. Update each affected file so that decisions, plans, links, progress, and open questions remain mutually consistent.
3. Remove or clearly supersede stale information instead of leaving contradictory notes.
4. Add a focused Markdown file when a subject becomes too detailed for the existing files.
5. Keep `MAIN.md` lean. It should contain the product goal, durable core decisions, architectural overview, and pointers to focused documents—not detailed implementation procedures or research dumps.
6. Do not rely on chat history as the only record of a requirement or decision.

## File Responsibilities

- `MAIN.md` — concise product purpose, durable requirements, architectural overview, security principles, and links to focused documentation.
- `IMPLEMENTATION_PLAN.md` — detailed architecture, chosen libraries, ordered implementation tasks, tests, risks, and definition of done.
- `ARCHITECTURE.md` — component responsibilities, Python/TypeScript build boundary, request flow, native/Docker runtime modes, and process model.
- `POLAR_API.md` — verified and pending OAuth/API knowledge, scopes, endpoints, rate limits, payload notes, and backfill constraints.
- `POLAR_AUTH_SETUP.md` — detailed GitHub-safe Polar client configuration, Fernet key lifecycle, callback behavior, synchronization, and troubleshooting.
- `DATA_MODEL.md` — persistence, schema, raw payload retention, training mappings, aggregate formulas, migrations, and backups.
- `UI.md` — timeline and training-chart behavior, mapping interface, visual references, accessibility, and light/dark themes.
- `DEPLOYMENT.md` — native and Docker startup, home-server configuration, scheduler behavior, storage, networking, backups, upgrades, and security.
- `TODOS.md` — concise current work queue and unresolved tasks; update it as implementation progresses rather than duplicating the full plan.
- `LOG.md` — dated record of important decisions and meaningful project milestones. Keep entries short and factual.
- `LINKS.md` — external references and short notes explaining why each link matters.
- `DOCUMENTATION.md` — documentation organization and maintenance rules.

## When to Create More Files

Create another focused document when a new subject would make an existing file difficult to scan. Do not create empty placeholders merely for completeness.

## Consistency Checklist

When documentation is updated, check:

- [ ] New requirements are recorded in the appropriate durable file.
- [ ] `MAIN.md` remains concise and points to detailed documents.
- [ ] `IMPLEMENTATION_PLAN.md` reflects architectural or acceptance-criterion changes.
- [ ] `TODOS.md` reflects the current next actions.
- [ ] `LOG.md` records important decisions or milestones with a date.
- [ ] `LINKS.md` contains newly relevant primary references.
- [ ] Obsolete or contradictory statements have been removed.
- [ ] No credentials, OAuth tokens, personal health records, or database contents are present in Markdown.
