# Contributing

Useful contributions include reproducible calculation failures, import examples, installation improvements and scientific tests. Open an issue with the operating system, Python/Node versions, a small non-confidential structure and the complete error message. Include the method, charge, multiplicity and solvent for calculation issues.

Use the local launcher to install the application, then install development dependencies with `.venv/bin/python -m pip install -r requirements-dev.txt` (Windows: `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`).

Run the checks documented in README.md before proposing a change. New numerical features should include real molecular examples, methods/units, scientific limitations and a regression test. Do not add inferred values for properties that the calculation engine did not compute.

Keep molecular data, databases, virtual environments and dependency directories out of commits. Use synthetic or public examples when reporting bugs. The GitHub validation workflow is configured for Linux; additional platform results should state exactly what was tested.
