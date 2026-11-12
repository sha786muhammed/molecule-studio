# Three runnable scientific examples

Start the application with `python3 launch.py`, then run `python3 examples/run_examples.py` in another terminal. The runner uses only the Python standard library and sends structures to the **local** API at `http://127.0.0.1:8765` by default.

| Example | What it demonstrates | Checks |
|---|---|---|
| Water | GFN2-xTB optimization and numerical harmonic frequencies | Converged finite energy in Hartree; neutral charge sum; broad dipole sanity interval; three positive internal modes |
| Ethanol | MMFF94 geometry optimization | Convergence, kcal/mol units, energy no higher than its starting value |
| Butane | ETKDGv3 sampling, MMFF94 optimization and RMSD deduplication | At least two sampled shapes, sorted converged energies, zero relative energy for the lowest found |

Each invocation creates a new project called Getting started examples. The output directory contains the full calculation records, coordinates and molecular structures, plus `summary.json`. Butane XYZ and SDF include all retained conformers. These files are intentionally excluded from git so your local runs do not enter the source repository.

Use `--base-url http://127.0.0.1:8766` for a different local port, or `--output /path/to/results` for a different output directory. Failed, unconverged or numerically inconsistent examples cause a nonzero exit status.

`reference-results.json` records one measured run with engine versions. Small numerical differences across platforms and dependency versions are possible. These checks validate these examples against physical/numerical invariants; they are not a general benchmark, comparison with experiment, or evidence that every molecule/method combination is validated.

Force-field and quantum energies are different quantities. The butane ranking does not establish the global minimum, free energies or thermodynamic populations. The water frequencies have rigid-body motion projected out; IR intensities and thermochemistry are not calculated.
