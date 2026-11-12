# Molecule Studio

A local molecular workbench: draw or import a molecule, generate 3D coordinates, run real calculations, inspect results, and compare or export them. Calculations run on your computer; no paid calculation service or API key is required. Molecule Studio is the working title of an independent early-stage project.

## Quick start

Install **Python 3.12+** and **Node.js 22+**, download/extract the project, then run this from its folder:

```bash
python3 launch.py
```

Windows: `py -3.12 launch.py`. The launcher installs dependencies into a separate `.venv`, builds the interface and opens **http://127.0.0.1:8765**. The first setup needs an internet connection. Your own computer runs the calculations; the launcher starts a single-user service on loopback only.

[Step-by-step setup and troubleshooting](docs/QUICKSTART.md) · [Runnable examples](examples/README.md) · [Contributing](CONTRIBUTING.md)

## Features
- Home, projects, searchable molecule library, calculation setup, job history, results, comparisons, documentation and settings.
- OpenChemLib 2D editor; SMILES, MOL/SDF and neutral XYZ import.
- Interactive molecular viewer, with a software renderer when WebGL is unavailable.
- RDKit descriptors: molecular weight, Wildman–Crippen cLogP, TPSA, hydrogen-bond counts, rings and rotatable bonds.
- MMFF94/UFF force-field optimization and single points.
- Conformer search: ETKDGv3 sampling, MMFF94/UFF optimization, symmetry-aware heavy-atom RMSD deduplication, ranked relative energies, selectable 3D structures and ensemble XYZ/SDF/JSON exports. Save a selected conformer for a separate xTB refinement.
- Real GFN2-xTB quantum optimization and single points through tblite/ASE, including energy, dipole, atomic charges and model orbital energies when available.
- ALPB water/ethanol/acetonitrile solvent support.
- Optional numerical harmonic frequencies for molecules with at most 18 atoms.
- SQLite project/molecule/job persistence and XYZ/SDF/JSON/CSV exports.

## Developer setup
Requires Python 3.12+ and Node.js 22+.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
STUDIO_PYTHON="$PWD/.venv/bin/python" npm run dev -- --host 127.0.0.1 --port 4173
```

The development launcher starts FastAPI on loopback port 8001 and Vite on the requested port. `/api` is proxied by Vite. For an isolated preview where Python dependencies must be mounted with the project, `python3 -m pip install --target .runtime/python -r requirements.txt` is also supported. Never commit `.runtime`, `.venv`, or `node_modules`.

For the built interface and API in one process, use `python3 launch.py`, or after installation/build run `.venv/bin/python -m backend.web`. The source uses a hash-based client router, so client pages share the same root document. API routes are registered before static files.

## Validation
```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s backend -p 'test_*.py' -v
npm run build
npm test
npm run test:sites
```

The GitHub workflow in `.github/workflows/validate.yml` runs the Python and JavaScript checks, builds the frontend, starts the local server and runs the three scientific examples. It has not run remotely until this source is published to a GitHub repository. Local validation and platform details are recorded in [docs/VALIDATION.md](docs/VALIDATION.md).

`npm run build` builds the static frontend and the retained starter hosting artifact. The static Worker does **not** host the Python calculation engine. For production deployment, run the Python service separately and configure a same-origin API gateway and authentication. Do not describe the static artifact as a hosted calculation service.

## Scientific interpretation
- GFN2-xTB is semiempirical tight binding, not DFT. Force-field energies are not electronic energies. Do not compare energies across methods, units, compositions or charge/spin states.
- Standard molecule preparation generates one ETKDG starting structure. The separate conformer-search task samples 1–100 candidates (default 30), optimizes them, excludes unconverged structures and removes duplicates at a heavy-atom RMSD threshold (default 0.5 Å). Seed 42 and engine version are recorded. This is bounded sampling, not an exhaustive global search. Inspect connectivity, stereochemistry, protonation and spin; hydrogen-only rearrangements may be merged.
- Ensemble energies are gas-phase force-field potential energies in kcal/mol. Relative energies refer only to the lowest converged sampled structure under the same method; no thermodynamic populations, free energies, or frequency verification are provided. MMFF/UFF rankings need not agree with quantum calculations. xTB refinement is a separate calculation for the selected saved structure.
- The xTB optimizer uses ASE BFGS, up to 180 steps, force threshold 0.03 eV/Å. Nonconvergence is reported.
- Coordinates: Å; xTB energies: Hartree; force-field energies: kcal/mol; dipoles: Debye; charges: e; frequencies: cm⁻¹. Charged-molecule dipoles depend on the origin.
- Frequency output projects rigid rotations and translations out of the mass-weighted Hessian before extracting internal modes. No IR intensities or thermochemistry are implemented.
- Limits: connected molecules up to 80 atoms including hydrogens, numerical frequencies up to 18 atoms, up to five queued/active jobs, one computational worker.

## Project layout
`src/` contains the React interface; `backend/chemistry.py` owns scientific operations; `backend/app.py` provides the HTTP API; `backend/storage.py` persists records in `backend/data/studio.sqlite3`. Database content is excluded from source distributions.

## Credits and licensing
Original application interface inspired by a scientific workbench layout. No Rowan source code, logo or brand assets are used. Scientific dependencies retain their own licenses: RDKit, OpenChemLib, 3Dmol.js, tblite and ASE. `public/vendor/3Dmol-LICENSE.txt` accompanies the bundled viewer. See upstream licenses before redistributing a combined application.

Original application code is released under the [MIT License](LICENSE). [Third-party notices](THIRD_PARTY.md) describe the separate upstream components. This local research edition does not include public hosting, authentication, DFT, IR intensities or thermochemistry.
