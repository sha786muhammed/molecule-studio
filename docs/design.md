# Molecule Studio

Use displayed design option 1: white scientific workspace, green primary actions, persistent left navigation, central 2D/3D molecule viewer and right calculation settings. Build every requested page and connect the molecular workflow to real open-source engines. This is a local single-user research application, not a production multi-tenant service.

Pages: Home, Projects, Molecules, New calculation, Calculations, Result details, Compare, Documentation and Settings. Support SMILES, MOL/SDF and XYZ imports, OpenChemLib drawing, saved SQLite projects/molecules/jobs, RDKit descriptors and 3D generation, MMFF94/UFF optimization and GFN2-xTB optimization/single points via tblite and ASE. Optional numerical frequencies are limited to small molecules. Show methods, units, convergence and errors, never fabricate quantum results. Compare only same-method energies for the same composition/charge/spin/solvent. Downloads include XYZ, SDF, JSON and CSV.

Implementation choices: React/Vite frontend, OpenChemLib CanvasEditor, 3Dmol molecular rendering, Phosphor icons, Python FastAPI API, SQLite storage, ASE/tblite calculations. Bind API to loopback; Vite proxies /api. No paid service or external molecular uploads. Public production hosting and authentication need separate deployment work.

Conformer milestone: use existing job history and results pages for deterministic ETKDGv3 candidate generation, MMFF94/UFF gas-phase optimization, heavy-atom RMSD deduplication and relative-energy ranking. Show a selectable 3D ensemble, CSV ranking, ensemble XYZ/SDF exports and a selected-geometry handoff to a separately submitted xTB optimization. State that sampling is bounded and energies are force-field potential energies, not free energies.
