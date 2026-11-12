# Molecule Studio Implementation Plan

> For agentic workers: implement natively in this session, task by task.

**Goal:** A complete navigable molecular calculation app with real local scientific engines.
**Architecture:** React frontend proxies a FastAPI service; SQLite persists projects, molecules and jobs. Chemistry is isolated from HTTP and persistence.
**Tech Stack:** React, Vite, OpenChemLib, 3Dmol, Phosphor, FastAPI, RDKit, tblite, ASE.
**Spec:** docs/design.md

## Global Constraints
- Match displayed visual option 1; label real methods and units.
- Reject invalid structures, incompatible spin/charge and unsupported force-field models.
- Never replace failures with invented results.
- All pages and visible primary controls work.

## Review Focus
- Invalid molecular input returns actionable errors.
- Geometry and energy units remain consistent across engines.
- Reopening the app preserves saved work.
- Failed and unconverged jobs do not display success.
- Comparing different species never implies a reaction or binding energy.

## Tasks
- [x] Test descriptors, input validation, force-field energy and quantum water charges/dipole against known invariants.
- [x] Implement backend/chemistry.py, backend/storage.py and backend/app.py, then pass scientific tests.
- [x] Implement navigation, molecule editor/viewer, projects, setup, jobs, results, comparison, docs and preferences.
- [x] Build frontend; run backend tests and verify browser workflow, persistence and exports.
- [x] Compare rendered workspace to reference; fix material issues and record design-qa.md.
- [x] Package source and save the deliverable.
