# Polar API Integration

## Principle

Use the official Polar AccessLink API rather than scraping the Polar Flow website. Store OAuth credentials/tokens only; never store the Polar account password.

## Setup Flow

The complete private configuration, local callback, token-encryption, Docker, troubleshooting, and GitHub publication procedure is in `POLAR_AUTH_SETUP.md`.

1. Create or use a Polar Flow account.
2. Create an API client at `https://admin.polaraccesslink.com`.
3. Save the generated client ID and client secret outside committed files.
4. Configure an allowed redirect URI.
5. Start the application's OAuth authorization-code flow.
6. Log in to Polar and approve access in the browser.
7. Exchange the short-lived authorization code for tokens.
8. Register the Polar user with AccessLink and store the encrypted access token for scheduled synchronization.

## OAuth Notes

Polar AccessLink API v3 uses a redirect-based OAuth authorization-code flow; it does not document a device-code flow. The authorization code expires after 10 minutes and must be exchanged exactly once. Reusing it deletes all issued tokens.

The verified v3 token endpoint is:

```text
https://polarremote.com/v2/oauth2/token
```

The documented token exchange uses HTTP Basic authentication with `client_id:client_secret`. The response contains an access token, token type, expiry (documented as about one year), and `x_user_id`; the v3 documentation does not specify a refresh token.

The redirect URI must exactly match one configured on the AccessLink client. The verified native-development URI is `http://localhost:8000/api/polar/callback`.

For this application, begin local OAuth at `http://localhost:8000/settings`, not `http://127.0.0.1:8000`. OAuth state is stored in a host-only browser cookie; `localhost` and `127.0.0.1` do not share it. Mixing those hosts causes the callback to fail state validation.

Use this local callback for development after registering it:

```text
http://localhost:8000/api/polar/callback
```

If setup occurs from another machine on the home network, investigate a LAN callback such as:

```text
http://home-server.local:PORT/callback
```

Allowed callback formats must be verified in the current Polar client administration. If Polar requires a public HTTPS callback, expose only the callback route temporarily through a narrow tunnel or reverse-proxy rule and remove it after setup.

## API Versions

Documentation currently referenced by the project:

- AccessLink API v3: `https://www.polar.com/accesslink-api/`
- AccessLink Dynamic API v4: `https://www.polar.com/polar-api-v4/`

Local, unmodified snapshots of the published v3 OpenAPI and v4 Swagger specifications are stored in `reference/polar-api/`. Their source URLs, retrieval date, and SHA-256 checksums are recorded in `reference/polar-api/README.md`. Generate Markdown from those specifications on demand; do not treat the snapshots as automatically current.

The implementation uses the documented AccessLink v3 endpoints for all current categories: exercises, sleep, Nightly Recharge, activities, and continuous heart rate. v4 remains unimplemented until its endpoint contract is independently verified.

## Required Data Categories

- Sleep summaries and stages
- Sleep wake vectors where available
- Nightly Recharge/recovery results
- Exercises and training sessions
- Activity summaries
- Continuous heart-rate samples where useful and storage-effective
- Sport metadata/identifiers
- Calendar entries if needed for training history

## Verified Scope

```text
accesslink.read_all
```

The v3 API documentation identifies `accesslink.read_all` as the scope for the required data endpoints.

## Implemented Sync Behavior

- Explicit request timeouts
- Bounded exponential backoff for rate limits and transient failures
- Respect `Retry-After`
- Idempotent imports using stable external IDs and uniqueness constraints
- Independent category transactions so one failure does not corrupt other categories
- Raw response retention before or atomically with normalization
- Redaction of tokens and personal payloads from logs

`POST /api/polar/sync` runs the five current v3 categories independently and returns `inserted`, `updated`, `skipped`, and `errors` counts for each. Repeat syncs are idempotent: records with identical raw payloads are reported as skipped/unchanged rather than duplicated. APScheduler invokes the same flow at the configured interval while one backend process is running.

## Verified v3 Data Endpoints and Units

- `GET /v3/exercises` returns only exercises uploaded in the past 30 days after client registration. Distance is metres and duration is ISO-8601; the service derives speed in metres/second and pace in seconds/kilometre.
- `GET /v3/users/sleep` and `GET /v3/users/nightly-recharge` return the most recent 28 days.
- `GET /v3/users/activities?from=YYYY-MM-DD&to=YYYY-MM-DD` accepts at most a 28-day range and cannot request dates more than 365 days old.
- `GET /v3/users/continuous-heart-rate?from=YYYY-MM-DD&to=YYYY-MM-DD` returns date-keyed samples; stored heart rate is bpm.
- Rate limits are dynamic: 500 + 20 per registered user over 15 minutes, and 5000 + 100 per registered user over 24 hours. Polar reports usage, limits, and reset timing in response headers.

## Research Required Before Endpoint Implementation

- [x] Verify current v3 authorization endpoint, token endpoint, authorization-code lifetime, and scope against official documentation.
- [x] Verify that the registered `http://localhost:8000/api/polar/callback` URI completes a local authorization flow.
- [ ] Verify whether LAN hostname callback URIs are accepted.
- [x] Confirm that no device-code flow is documented for AccessLink v3.
- [ ] Identify exact v4 endpoints and payloads for every required category.
- [ ] Identify any required field available only through v3.
- [ ] Verify short-term and long-term rate limits.
- [ ] Verify pagination, historical availability, and practical backfill limits.
- [ ] Document source units and timezone behavior for training fields.
