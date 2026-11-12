# Third-party software

The application combines existing scientific engines and interface libraries. The original application license does not replace their licenses or their scientific citation requirements.

| Component | Role | Upstream |
|---|---|---|
| RDKit | Structure parsing, descriptors, embedding, force fields and conformer comparison | https://www.rdkit.org/ |
| tblite | GFN2-xTB electronic calculations | https://github.com/tblite/tblite |
| ASE | Optimization and numerical vibrations | https://ase-lib.org/ |
| NumPy and SciPy | Numerical operations | https://numpy.org/ and https://scipy.org/ |
| FastAPI and Uvicorn | Local HTTP service | https://fastapi.tiangolo.com/ and https://www.uvicorn.org/ |
| OpenChemLib | Interactive 2D editor (BSD-3-Clause) | https://github.com/cheminfo/openchemlib-js |
| 3Dmol.js | Molecular visualization (BSD-3-Clause) | https://github.com/3dmol/3Dmol.js |
| React, Vite and Phosphor icons | Application interface and build tooling (MIT) | https://react.dev/, https://vite.dev/, https://phosphoricons.com/ |

The vendored 3Dmol.js browser build is accompanied by its upstream license in `public/vendor/3Dmol-LICENSE.txt`. Package managers install the remaining packages with their own license files. Review the licenses of bundled dependencies when distributing compiled or self-contained packages.

The interface is an original implementation inspired by scientific workbench conventions. This project is independent of Rowan and does not include Rowan source code, branding, or assets. “Molecule Studio” remains a working title.
