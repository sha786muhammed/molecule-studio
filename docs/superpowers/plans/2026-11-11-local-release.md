# Free Local Release Implementation Plan

**Goal:** Prepare a GitHub-ready local application that researchers can install and run without a hosted calculation service.

**Architecture:** A standard-library Python launcher creates a project-local virtual environment, installs dependencies, builds the existing React interface, and launches one loopback-only FastAPI process that serves both the API and built frontend. Preserve the existing Vite development preview and scientific engine. Retain user data in SQLite outside distributable archives.

**Tech stack:** Python 3.12+, Node.js 22+, existing FastAPI/RDKit/tblite/ASE/React dependencies. No additional paid service, container runtime, or account required.

## Scope and constraints
- Existing single-user scope, scientific limits and method labels stay in force.
- `python3 launch.py` is the documented macOS/Linux command; `py -3.12 launch.py` is the Windows equivalent after prerequisites are installed.
- Launcher subprocesses must use the isolated environment, resolve files relative to the project, stop on installation failures, and bind only to 127.0.0.1. Keep data when stopping or updating.
- Static serving exposes only `dist/client`; missing API routes must stay errors rather than becoming HTML pages.
- Ship runnable water xTB/frequency, ethanol MMFF94, and butane conformer examples with measured reference summaries.
- Add a GitHub validation workflow and contribution guidance. Do not claim GitHub publication, remote CI success, or Windows/macOS verification from local Linux tests.

## Tasks
- [x] Add failing local-server tests for real API startup, built asset serving, and file/API boundaries; implement `backend/web.py`.
- [x] Add `launch.py` with isolated installation, dependency fingerprinting, prerequisite checks, browser opening, and clean shutdown.
- [x] Add a standalone HTTP example runner, reference results, quickstart, contribution notes and CI workflow.
- [x] Verify a fresh environment using the actual launcher, run examples and all tests/build checks. Browser inspection was attempted but blocked by preview connection failures; see `docs/VALIDATION.md`.
- [x] Prepare the updated source archive excluding environments, dependencies, databases and generated example runs.

## Outcome

Fresh Linux installation, 18 Python tests, 6 JavaScript tests, production build and the complete launcher/example/shutdown workflow passed. The separate Sites check passed its four tests, already counted in the JavaScript suite. Included MIT licensing for original code, upstream viewer license text, setup/contribution documentation, and a GitHub validation workflow. GitHub publication, public hosting and cross-platform verification are not claimed.

## Verification focus
- Missing Python/Node and dependency installation failures must give actionable errors.
- A non-project working directory must not break launch paths.
- Existing SQLite data must remain separate from installation state.
- Unknown API endpoints and repository files must not be served as frontend content.
- The example runner must check convergence, units, and numerical sanity, not simply HTTP success.
