# Methods and scientific interpretation

- GFN2-xTB is semiempirical tight binding, not DFT. Force-field energies are not electronic energies. Do not compare energies across methods, units, compositions or charge/spin states.
- Standard molecule preparation generates one ETKDG starting structure. The separate conformer-search task samples 1–100 candidates (default 30), optimizes them, excludes unconverged structures and removes duplicates at a heavy-atom RMSD threshold (default 0.5 Å). Seed 42 and engine version are recorded. This is bounded sampling, not an exhaustive global search. Inspect connectivity, stereochemistry, protonation and spin; hydrogen-only rearrangements may be merged.
- Ensemble energies are gas-phase force-field potential energies in kcal/mol. Relative energies refer only to the lowest converged sampled structure under the same method; no thermodynamic populations, free energies, or frequency verification are provided. MMFF/UFF rankings need not agree with quantum calculations. xTB refinement is a separate calculation for the selected saved structure.
- The xTB optimizer uses ASE BFGS, up to 180 steps, force threshold 0.03 eV/Å. Nonconvergence is reported.
- Coordinates: Å; xTB energies: Hartree; force-field energies: kcal/mol; dipoles: Debye; charges: e; frequencies: cm⁻¹. Charged-molecule dipoles depend on the origin.
- Frequency output projects rigid rotations and translations out of the mass-weighted Hessian before extracting internal modes. No IR intensities or thermochemistry are implemented.
- Limits: connected molecules up to 80 atoms including hydrogens, numerical frequencies up to 18 atoms, up to five queued/active jobs, one computational worker.


See [third-party notices](../THIRD_PARTY.md) for scientific software credits. Hosted demo limits are lower; see [deployment](DEPLOYMENT.md).
