# Conformer Search Implementation Plan

**Goal:** Extend the existing workbench with a reproducible, bounded conformer search and selectable results.

**Architecture:** Keep the existing single-worker job queue and SQLite records. Add an RDKit ETKDGv3 → MMFF94/UFF optimization → symmetry-aware heavy-atom RMSD deduplication task. Existing single-structure calculations remain unchanged.

**Tech stack:** Existing React, FastAPI and RDKit dependencies.

## Design decisions
- Add “Conformer search” to New calculation. Support MMFF94/UFF, gas phase, closed shell, 1–100 candidate structures, RMSD threshold 0.1–2 Å (default 0.5), fixed seed 42.
- Rank only converged structures by force-field energy in kcal/mol. Record generated, nonconverged and duplicate counts; fail clearly if none converge. Show relative energies, not thermodynamic populations or a claim of a global minimum.
- Results show an ensemble table, selectable 3D geometry, selected XYZ download and an action to save a selected conformer for an existing xTB optimization.
- Full SDF/XYZ exports contain the ensemble; JSON preserves search settings and metadata. Single-structure jobs keep their existing export behavior.
- Keep the current white/green workbench design. Leave the working title unchanged until a new name is selected.

## Tasks
- [x] Write failing scientific tests for butane diversity, ranking, deduplication, deterministic output and invalid settings.
- [x] Implement conformer generation, optimization, RMSD filtering and provenance in `backend/conformers.py`; dispatch through `backend/chemistry.py`.
- [x] Write failing API tests, extend job validation and exports, and verify persisted ensemble records and selected geometry downloads.
- [x] Add setup controls and `src/ConformerResults.jsx`, connect selected conformers to a new optimization, and update job labels and documentation.
- [x] Run the Python suite, JavaScript suite and production build. Exercise the complete workflow in the preview, then save the updated source archive.

## Validation
- 13 Python tests and 6 JavaScript tests pass. Production build succeeds with the existing large-bundle warning from the molecular editor.
- Preview: add butane → sample 30 shapes → retain 2 distinct conformers (28 duplicates) → select conformer 2 (ΔE 0.782 kcal/mol) → save it for xTB → submit and complete quantum optimization.
- API tests parse every exported ensemble SDF record, verify multi-frame XYZ and selected-conformer XYZ, and check SQLite persistence. Browser download completion is not claimed.
- Updated development-test dependency to httpx2 because the installed Starlette TestClient requires it.

## Review focus
- Rigid molecules may produce only one unique conformer: report successful deduplication.
- Preserve stereochemistry and connectivity; use the molecule graph and explicit hydrogens.
- Never mix force-field and quantum energies or rank unconverged candidates.
- Deterministic generation must retain seed, settings and RDKit version.
- Ensemble exports must contain distinct structures and correct per-structure metadata.
