"""Bounded conformer sampling; energies are force-field potential energies."""
import time
import numpy as np
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, rdMolAlign
from backend.chemistry import coordinates, xyz_text


def search_conformers(molecule, settings, progress=None):
    started = time.time()
    method = settings['method']
    count = settings.get('conformer_count', 30)
    threshold = float(settings.get('rmsd_threshold', 0.5))
    mol = Chem.MolFromMolBlock(molecule['molblock'], removeHs=False)
    mol.RemoveAllConformers()
    if method == 'MMFF94':
        if not AllChem.MMFFHasAllMoleculeParams(mol):
            raise ValueError('MMFF94 parameters are missing. Try UFF.')
        properties = AllChem.MMFFGetMoleculeProperties(mol)
    elif not AllChem.UFFHasAllMoleculeParams(mol):
        raise ValueError('UFF parameters are missing for this molecule.')

    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = 42
    parameters.numThreads = 1
    parameters.pruneRmsThresh = -1.0  # Deduplicate only after optimization.
    parameters.enforceChirality = True
    identifiers = list(AllChem.EmbedMultipleConfs(mol, numConfs=count, params=parameters))
    if not identifiers:
        raise ValueError('No conformers could be embedded. Check the structure or import another geometry.')
    candidates = []
    failed = []
    for index, identifier in enumerate(identifiers):
        if method == 'MMFF94':
            ff = AllChem.MMFFGetMoleculeForceField(mol, properties, confId=identifier)
        else:
            ff = AllChem.UFFGetMoleculeForceField(mol, confId=identifier)
        initial = float(ff.CalcEnergy())
        status = ff.Minimize(maxIts=1000, forceTol=1e-4, energyTol=1e-8)
        energy = float(ff.CalcEnergy())
        if status != 0 or not np.isfinite(energy):
            failed.append(index + 1)
        else:
            candidates.append((energy, identifier, initial))
        if progress:
            progress(index + 1, energy if np.isfinite(energy) else None, 'kcal/mol')
    if not candidates:
        raise ValueError(f'None of the {len(identifiers)} generated conformers converged. No energy ranking was produced.')

    candidates.sort(key=lambda entry: (entry[0], entry[1]))
    heavy = Chem.RemoveHs(mol)
    kept = []
    for energy, identifier, initial in candidates:
        # GetBestRMS aligns its probe in place: copy to preserve output coordinates.
        duplicate = any(rdMolAlign.GetBestRMS(
            Chem.Mol(heavy), heavy, prbId=identifier, refId=previous,
            maxMatches=10000) < threshold for _, previous, _ in kept)
        if not duplicate:
            kept.append((energy, identifier, initial))

    conformers = []
    minimum = kept[0][0]
    for rank, (energy, identifier, initial) in enumerate(kept, 1):
        selected = Chem.Mol(mol)
        geometry = Chem.Conformer(mol.GetConformer(identifier))
        selected.RemoveAllConformers()
        selected.AddConformer(geometry, assignId=True)
        atoms = coordinates(selected)
        relative = energy - minimum
        conformers.append({
            'rank': rank, 'sample_id': identifier + 1, 'energy': energy,
            'relative_energy': relative, 'initial_energy': initial,
            'energy_unit': 'kcal/mol', 'converged': True, 'atoms': atoms,
            'molblock': Chem.MolToMolBlock(selected),
            'xyz': xyz_text(atoms, f'{molecule["name"]}; conformer {rank}; {method}; E={energy:.10f} kcal/mol; relative={relative:.6f} kcal/mol'),
        })
    best = conformers[0]
    notes = [
        'Gas-phase force-field potential energies, not electronic or Gibbs free energies.',
        'ETKDGv3 samples conformations with specified stereochemistry enforced. Unspecified stereochemistry is not resolved by this search.',
        'Only converged structures are ranked. Symmetry-aware heavy-atom RMSD removes optimized duplicates; hydrogen-only rearrangements may be merged.',
        'The lowest energy shown is the lowest among sampled structures, not a proven global minimum. Frequencies and thermodynamic populations are not calculated.',
    ]
    if failed:
        notes.append(f'{len(failed)} generated structures did not converge and were excluded from the ranking.')
    return {
        **best, 'method': method, 'task': 'conformers', 'conformers': conformers,
        'search': {'generator': 'ETKDGv3', 'seed': 42, 'requested': count,
                   'generated': len(identifiers), 'converged': len(candidates),
                   'unconverged_sample_ids': failed,
                   'duplicates_removed': len(candidates) - len(kept), 'unique': len(kept),
                   'rmsd_threshold_angstrom': threshold, 'rmsd_atoms': 'heavy atoms',
                   'rmsd_symmetry_max_matches': 10000, 'max_iterations': 1000},
        'dipole': None, 'charges': None, 'orbitals': None, 'frequencies': None,
        'modes': None, 'history': [], 'converged': True,
        'engine': f'RDKit {rdBase.rdkitVersion}', 'settings': dict(settings),
        'duration': round(time.time() - started, 2), 'notes': notes,
        'coordinate_unit': 'angstrom',
    }
