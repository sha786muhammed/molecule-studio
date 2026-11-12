# Molecule Studio design QA

final result: passed

## Evidence and state
- Source visual truth: `/workspace/scratch/c325754f17d2/generated_images/exec-4473cfd3-437a-4b3b-a000-a77fc9a68d8d.png` (first displayed option).
- Browser-rendered implementation: `/workspace/scratch/molecule-studio-final.jpg`.
- Full-view comparison: `/workspace/scratch/c325754f17d2/qa-comparison.jpg`.
- Focused configuration comparison: `/workspace/scratch/c325754f17d2/qa-details.jpg`.
- State: New calculation, Caffeine, 3D view, GFN2-xTB, gas phase, neutral singlet.
- CSS viewport observed: 1363 × 936. Source raster: 1487 × 1058; captured implementation raster: 1168 × 936. Browser screenshot output and source have different bounds; comparison uses aspect-preserving scaling to 1100-pixel-wide panes. No pixel-exact equivalence is claimed. The full-page capture attempt timed out; the subsequent standard screenshot captured the complete workbench composition.
- Desktop checked. CSS responsive breakpoints implemented; mobile browser capture was not performed.

## Findings and comparison history
1. [P1, fixed] WebGL is unavailable in this browser. Original viewer initialization threw and unmounted the app. Added a coordinate- and bond-driven Canvas2D molecular renderer with rotation/zoom, keeping 3Dmol.js for browsers with WebGL.
2. [P2, fixed] React StrictMode left an extra blank canvas. Capture the host element in effect cleanup and clear it before viewer initialization. Final DOM has one molecular canvas and displays the real structure.
3. [P2, fixed] Molecule appeared small in its canvas. Adjusted software-viewer initial fit to 1.3. Final side-by-side comparison shows an appropriately prominent molecule without clipping.
4. [P2, fixed] Export comparison could briefly export a stale selection while new results loaded. Disabled export during loading; confirmed both selected molecules appear in the final comparison.
5. No remaining actionable P0/P1/P2 visual findings in the reviewed desktop state.

## Required fidelity surfaces
- Typography: clean DM Sans/Arial scientific UI, bold title, regular form controls and clear section hierarchy. Main labels and navigation remain readable. Small secondary provenance copy is intentionally quiet. Source mock used larger form labels; functional layout adds a task selector and method explanation.
- Spacing/layout: source composition is preserved: persistent sidebar, breadcrumb, large title, central molecule/editor and right settings panel. Simple dividers separate properties and controls. No horizontal viewport overflow was observed. Home/job-history navigation and added provenance require intentional deviations from the initial static mock.
- Colors/tokens: white base, near-black headings, muted gray metadata and restrained green primary/selected states. Error, running and completed states remain distinct.
- Image quality: actual chemical coordinates and bonds are rendered interactively, rather than using a raster mock molecule. RDKit supplies exact 2D depictions; standard Phosphor icons supply UI marks. The mock molecule's orientation is intentionally not preserved because real scientific structures replace its generated illustration.
- Copy/content: static preview labels are replaced by real method/engine status, actual descriptors, real results and meaningful validation. No invented computation results. Quantum/force-field units and limits are explicit.

## Browser interactions tested
All nine pages were visited: Home, Projects, Molecules, New calculation, Calculations, Results, Compare, Documentation, Settings. Created and saved a project and acetone structure; rejected malformed SMILES; opened the drawing editor; switched 2D/3D; ran GFN2-xTB water optimization with frequencies and acetone optimization; inspected charges and three projected internal water modes; compared results; downloaded charges/comparison CSV; saved preferences. Projects/molecules/jobs survived restart. Last application-error check returned no application errors; extension metadata errors were excluded.

## Verification limits
- XYZ/SDF/JSON HTTP attachment exports are implemented. The API integration test verifies XYZ content and attachment headers. Browser download-event capture repeatedly timed out for XYZ, so automated browser download confirmation remains inconclusive. CSV event capture succeeded.
- The build emits a static frontend/retained Worker artifact. Python computation runs in the local service and is not deployed by that static Worker. Public hosting and multi-user authentication are not implemented.
- Vite reports large frontend chunks (OpenChemLib); this is performance follow-up, not a functional build failure.

## Implementation checklist
- [x] Real chemistry engines and explicit units/provenance.
- [x] Connected navigation and core forms.
- [x] Persistent local projects, molecules and calculation history.
- [x] End-to-end browser calculation workflow.
- [x] Full-view and focused-region visual review.
- [x] Eight scientific/API tests and six frontend/packaging tests pass.
- [ ] Follow-up: independent mobile QA, download-event confirmation, lazy-load editor, production deployment/authentication.
