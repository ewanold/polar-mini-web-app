# Polar OAuth Setup and GitHub-Safe Configuration

## Purpose

This guide configures one private Polar AccessLink client for this application. It covers the local authorization flow, encrypted token storage, synchronization, Docker configuration, and the checks required before publishing the repository to GitHub.

The application uses Polar's browser-based OAuth authorization-code flow. It never asks for or stores a Polar account password.

## Security Boundary

Keep these values private:

- Polar OAuth client secret
- Fernet token-encryption key
- OAuth authorization codes and access tokens
- `.env` and `database/polar-app.sqlite3`

Do not place them in Markdown, source code, issues, screenshots, terminal output shared publicly, or Git commits. `.env` and `database/` are ignored by Git; `.env.example` is the safe committed template.

A Polar client ID is not treated as a password, but it should still be omitted from public documentation unless there is a deliberate reason to expose it.

## 1. Create the Polar AccessLink Client

1. Create or sign in to a Polar Flow account at <https://flow.polar.com>.
2. Open the Polar AccessLink administration portal: <https://admin.polaraccesslink.com>.
3. Create a client and record its OAuth client ID and client secret. Treat the secret as a password.
4. Register this exact local redirect URI for native development:

   ```text
   http://localhost:8000/api/polar/callback
   ```

5. Ensure the registered URI and local configuration match character-for-character.

Polar's primary setup reference is <https://www.polar.com/accesslink-api/>.

## 2. Create Local Configuration

From the repository root, copy the safe template without committing the new file:

```bash
cp .env.example .env
```

Set the following entries in `.env`:

```dotenv
POLAR_APP_POLAR_CLIENT_ID=your_client_id
POLAR_APP_POLAR_CLIENT_SECRET=your_client_secret
POLAR_APP_POLAR_REDIRECT_URI=http://localhost:8000/api/polar/callback
POLAR_APP_POLAR_TOKEN_ENCRYPTION_KEY=your_fernet_key
```

The backend's Pydantic settings use the `POLAR_APP_` prefix. Older variable names such as `POLAR_CLIENT_ID` are not read by the native application.

Do not use quotes unless they are part of the value. Do not add `.env` to Git.

## 3. Generate the Fernet Token-Encryption Key

The Fernet key is generated locally; Polar does not provide it. It encrypts the Polar access token before that token is written to SQLite.

Generate one key once, then copy the single output line into `.env`:

```bash
UV_PROJECT_ENVIRONMENT="$HOME/.cache/polar-web-app/backend-venv" \
"$HOME/.hermes/bin/uv" run --project src/backend python -c \
'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Keep this key stable and backed up in a private secret manager. Changing or losing it makes existing stored tokens unreadable. In that case, delete the stored Polar connection and authorize again; never try to recover the token by publishing the old key.

If authorization failed before the callback exchanged a token, generating a replacement key has no data effect. After a successful connection, do not regenerate it.

## 4. Build and Start the Native Application

This repository is on a `noexec` CIFS mount, so invoke repository scripts through `bash`:

```bash
bash scripts/build.sh
bash scripts/run.sh
```

Open the application at:

```text
http://localhost:8000/settings
```

Do not begin the OAuth flow at `http://127.0.0.1:8000`. The state cookie is host-only. If the browser starts at `127.0.0.1` but Polar redirects to `localhost`, the callback cannot send the state cookie and the application rejects it with `400 Polar OAuth state validation failed`.

## 5. Authorize Polar

1. On **Settings**, confirm the page says Polar is not connected.
2. Select **Connect Polar**.
3. Sign in to Polar Flow and grant consent.
4. Polar redirects to `/api/polar/callback`.
5. Return to Settings and confirm it reports a connected Polar user.

A `307` response for `GET /api/polar/connect` is expected: it redirects the browser to Polar. Polar can redirect straight back without showing a login page when the browser already has a Polar Flow session.

An authorization code is short-lived and single-use. Do not retry a failed callback URL, paste it into another browser, or share it in logs. Start a fresh Connect Polar flow instead.

## 6. Synchronize and Interpret Results

On Settings, choose **Sync now**. The application requests the current Polar data categories and shows, for each category:

- **new** — records first written to the local database
- **updated** — known records whose source payload changed
- **unchanged** — records already present with unchanged source data
- **errors** — records that could not be processed in that category

A second sync normally reports existing records as unchanged rather than new. That is the expected idempotent behavior.

Current v3 source windows are limited by Polar. In particular, activities are requested for the last 28 days; training exercises are only available for the documented retention window after client registration. A zero result is valid when Polar has no available record for that category or window.

## 7. Docker Configuration

Docker Compose obtains substitution values from the repository-root `.env`. Its container environment must use the same prefixed settings as the native process:

```dotenv
POLAR_APP_POLAR_CLIENT_ID=your_client_id
POLAR_APP_POLAR_CLIENT_SECRET=your_client_secret
POLAR_APP_POLAR_REDIRECT_URI=http://localhost:8000/api/polar/callback
POLAR_APP_POLAR_TOKEN_ENCRYPTION_KEY=your_fernet_key
```

For a browser on another machine, `localhost` refers to that browser's machine, not necessarily the server. Before deploying beyond one local machine, register a stable trusted hostname and HTTPS callback with Polar, set `POLAR_APP_POLAR_REDIRECT_URI` to that exact public callback, and access the app through the same hostname. Do not use a public port-forward without authentication and HTTPS.

## Troubleshooting

| Symptom | Likely cause and action |
|---|---|
| `503 Polar OAuth client credentials are not configured` | The `.env` values are absent, use incorrect names, or the process was not restarted after editing `.env`. |
| `400 Polar OAuth state validation failed` | The application was opened under a different hostname than the configured callback. Use `http://localhost:8000/settings` for the local callback above and start a fresh authorization attempt. |
| Polar displays a generic OAuth error | Check the client ID, registered redirect URI, and current Polar client configuration. The URI must be exact. |
| `Polar rejected the authorization code` | The code expired, was already used, or the redirect URI/client configuration differs from the authorization request. Start a fresh authorization flow. |
| The app is connected but synchronization fails to decrypt the token | The Fernet key was changed. Restore the original private key or disconnect and reauthorize Polar. |
| A repeat sync says `0 new` | Inspect updated and unchanged counts. Existing records are intentionally not duplicated. |

## GitHub Publication Checklist

Before adding a remote or pushing:

1. If this checkout has no Git repository yet, initialize it before staging anything:

   ```bash
   git init
   git branch -M main
   ```

   Create the remote repository as private until the checklist is complete. Do not run `git add .` blindly.

2. Inspect the pending files:

   ```bash
   git status --short
   git diff -- . ':!database/**'
   ```

3. Confirm ignored secrets remain ignored:

   ```bash
   git check-ignore -v .env database/polar-app.sqlite3
   ```

4. Search only tracked/documentation/source files for accidental placeholder substitutions. Do not print `.env` or database contents while reviewing:

   ```bash
   git grep -nE 'POLAR_APP_POLAR_(CLIENT_SECRET|TOKEN_ENCRYPTION_KEY)=[^[:space:]]+'
   ```

   The command should find only empty template assignments or documentation examples using placeholders such as `your_client_secret`.

5. Stage only reviewed files, then inspect the staged diff before committing:

   ```bash
   git add .gitignore .env.example AI src scripts compose.yaml Dockerfile
   git diff --cached --check
   git diff --cached
   ```

6. Ensure `.env`, SQLite data, client secret, Fernet key, authorization codes, access tokens, and personal Polar data are absent from the staged diff.
7. If a secret was ever committed or posted publicly, rotate the Polar client secret, generate a new Fernet key, delete/reconnect the stored Polar token, and remove the secret from Git history before publishing further.

## Related Documents

- `POLAR_API.md` — verified endpoints, scopes, retention windows, and synchronization behavior
- `DEPLOYMENT.md` — native/Docker operation and network boundaries
- `DATA_MODEL.md` — encrypted OAuth token persistence and source-data tables
- `UI.md` — Settings connection and manual-sync interface
- `LINKS.md` — primary Polar references
