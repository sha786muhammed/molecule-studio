# Run Molecule Studio on your computer

The local edition runs calculations on your computer and opens the interface in your browser. No hosted calculation account, API key, subscription or GPU is required. The first setup downloads open-source dependencies and needs an internet connection.

## 1. Install the prerequisites

- Python **3.12 or newer**: https://www.python.org/downloads/
- Node.js **22 or newer**, including npm: https://nodejs.org/

On Windows, enable the Python installer option to add Python to PATH. On Linux, some distributions also require their `python3-venv` package. These instructions target Windows, macOS and Linux; the recorded release verification is Linux with Python 3.12. Other platforms are not yet independently verified.

## 2. Download and extract the project

Use the repository's **Code → Download ZIP**, or download the source archive supplied with the project. Extract it into a folder you can write to. Open a terminal in the folder containing `launch.py`, `package.json` and `requirements.txt`.

## 3. Launch

macOS or Linux:

```bash
python3 launch.py
```

Windows:

```powershell
py -3.12 launch.py
```

The launcher creates `.venv`, installs Python packages there, installs the interface packages in `node_modules`, builds the interface and starts one local server. It prints **http://127.0.0.1:8765** and opens it in your default browser. The first run takes longer because of downloads. Keep the terminal open while you use the app.

The launcher does not install packages into your system Python. It reuses its local dependencies on subsequent launches and rebuilds the interface. Press **Ctrl+C** in the terminal to stop.

## 4. Try a calculation

1. Select Water in New calculation.
2. Choose GFN2-xTB, Geometry optimization, charge 0, multiplicity 1 and Gas phase.
3. Optionally enable frequencies: water is within the 18-atom limit.
4. Run the calculation. Inspect energy, dipole, charges and frequencies in Results.
5. For a conformer search, add Butane with SMILES `CCCC`; choose Conformer search and MMFF94. Select an optimized structure and use Refine with xTB to prepare a separate quantum optimization.

Run the three automated examples in a **second** terminal while the app is running:

```bash
python3 examples/run_examples.py
```

On Windows, use `py -3.12 examples/run_examples.py`. Each run creates a new example project and writes JSON, XYZ and SDF output under `examples/results`. See `examples/README.md` for interpretation and the recorded reference results.

## Saved work and updates

Projects, molecules and jobs live in `backend/data/studio.sqlite3`. Stop the app before copying the database as a backup. The Settings page also exports a workspace JSON record; JSON import/restore is not implemented.

When replacing the source folder with a newer download, preserve the entire `backend/data` folder. Alternatively keep data separately:

```bash
python3 launch.py --data-dir /path/to/your/studio-data
```

Use the same `--data-dir` on every launch. This directory is separate from `.venv` and `node_modules` and is not removed by the launcher.

## Troubleshooting

| Problem | What to do |
|---|---|
| Python is too old | Install Python 3.12+ and invoke that version, e.g. `python3.12 launch.py`. |
| Node.js or npm is missing | Install Node.js 22+ LTS, reopen the terminal, then retry. |
| `venv` or `ensurepip` is unavailable on Linux | Install your distribution's matching Python venv package, then retry. |
| Dependency download fails | Read the package error, check the internet connection and rerun. Existing scientific data is retained. |
| A required wheel is unavailable for the platform | Try a supported 64-bit Python 3.12 installation; report the OS, architecture and exact package error. Platform compatibility has not been verified beyond the recorded Linux test. |
| Port 8765 is in use | Run `python3 launch.py --port 8766`. |
| Browser does not open | Open the printed local address manually, or use `--no-browser`. |
| App closes when terminal closes | Keep the launcher terminal open for the duration of your session. |
| Calculation fails or does not converge | Inspect the recorded error and method settings. Check formal charge, multiplicity and whether the method supports the molecule. |

To check Python/Node availability without installing anything, run `python3 launch.py --check`. To install/build without starting the app, use `--setup-only`.

The server binds to **127.0.0.1**, so it is for the computer running it. A phone or another computer cannot access this local address. The current release has no accounts or private per-user workspaces for shared online hosting.
