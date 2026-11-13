# A free website with a real calculation backend

**[Open the hosted demo](https://molecule-studio.onrender.com)** — deployed and smoke-checked on 13 November 2026. Use the instructions below to host your own copy.

The included Render Blueprint runs the React frontend and FastAPI/Python engine together at one HTTPS address. Calculations run on the server, so visitors can use a phone without installing Python.

## Deploy

1. [Open the prepared deployment](https://render.com/deploy?repo=https://github.com/sha786muhammed/molecule-studio) and sign in to Render.
2. Select your workspace. If prompted, connect only the `molecule-studio` GitHub repository. Review: one Docker web service, **Free** instance, no databases or persistent disks.
3. Deploy. After the Docker build completes, open the actual HTTPS URL Render shows; the service name might receive a suffix.
4. Test Water → GFN2-xTB → Single-point energy. Export the completed result as XYZ or JSON. In a private browser window, confirm that the first browser's calculation is absent.

Do not select paid compute or add a card just to run this demo. If Render requires paid verification for your account, stop: this configuration does not authorize a charge. Account-specific eligibility has not been verified.

## Free-plan limits

Render's documentation, checked 13 November 2026:

- 0.1 CPU and 512 MB RAM. Small calculations are the intended use; xTB and frequencies can be slow.
- Sleeps after 15 minutes without inbound traffic; waking takes about one minute.
- Local files, including SQLite records, disappear on sleep, restart or redeploy. Download results and workspace backups before leaving.
- 750 free instance hours per workspace per month, shared across services. Bandwidth and build-minute allowances also apply. Without a payment method, exhausting these allowances suspends services or builds rather than charging you.

Sources: [Free instances](https://render.com/docs/free), [Blueprint plans](https://render.com/docs/blueprint-spec#plan).

## Temporary browser workspaces

Each browser receives a signed, HttpOnly, Secure, SameSite cookie and separate SQLite file. Visitors cannot list another workspace's records, submit another visitor's molecule IDs, or download another visitor's exports. Background calculations retain their owner's workspace. Cookies expire after 24 hours; stale workspace files are removed when a new workspace is initialized.

The shared free process permits 40 atoms including hydrogen, 9 atoms for frequencies, 30 conformer candidates, 5 projects, 20 molecules and 10 submitted jobs per workspace. Each workspace can have one pending calculation; three pending/running calculations are allowed globally, with one worker. At most 64 temporary workspaces can be stored.

This is a public research demo with browser isolation, not an authenticated private research service. Do not upload confidential or unpublished structures. Cookies do not provide account recovery or durable storage. For private, persistent work use `python3 launch.py` on your own computer.

## Container

The local launcher still binds to loopback. Docker explicitly enables `STUDIO_DEMO=1` and starts `backend.hosted:create_hosted_app` on `0.0.0.0` using the provider's `PORT` (default 10000), with one server worker. The image excludes local databases, secrets and virtual environments. Render generates `STUDIO_SESSION_SECRET` without storing it in GitHub; otherwise a random per-process key is used.

Hosted API integration tests exercise real calculations and visitor separation. A successful provider build and live calculation are still required before calling an installation deployed.
