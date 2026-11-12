"""Scientific regressions: ranking, post-optimization duplicates and provenance."""
import unittest
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolAlign
from backend.chemistry import prepare_molecule, run_calculation, validate_settings


class ConformerTests(unittest.TestCase):
    def settings(self, **changes):
        return dict(method='MMFF94', task='conformers', charge=0,
                    multiplicity=1, solvent='gas', frequencies=False,
                    conformer_count=30, rmsd_threshold=0.5, **changes)

    def test_butane_has_distinct_ranked_optimized_shapes(self):
        molecule = prepare_molecule('CCCC', 'smiles', 'Butane')
        result = run_calculation(molecule, self.settings())
        conformers = result['conformers']
        self.assertGreaterEqual(len(conformers), 2)
        self.assertLessEqual(len(conformers), 3)
        energies = [c['energy'] for c in conformers]
        self.assertEqual(energies, sorted(energies))
        self.assertAlmostEqual(conformers[0]['relative_energy'], 0.0, places=8)
        self.assertGreater(conformers[-1]['relative_energy'], 0.1)
        self.assertTrue(all(c['converged'] for c in conformers))
        self.assertEqual(result['energy_unit'], 'kcal/mol')
        self.assertEqual(result['search']['seed'], 42)
        self.assertEqual(result['search']['generated'], 30)
        for i, first in enumerate(conformers):
            for second in conformers[i+1:]:
                a = Chem.RemoveHs(Chem.MolFromMolBlock(first['molblock'], removeHs=False))
                b = Chem.RemoveHs(Chem.MolFromMolBlock(second['molblock'], removeHs=False))
                self.assertGreaterEqual(rdMolAlign.GetBestRMS(a, b), 0.499)

    def test_rigid_water_collapses_to_one_and_search_repeats(self):
        molecule = prepare_molecule('O', 'smiles', 'Water')
        settings = self.settings()
        settings['conformer_count'] = 8
        first = run_calculation(molecule, settings)
        second = run_calculation(molecule, settings)
        self.assertEqual(len(first['conformers']), 1)
        self.assertEqual(first['search']['duplicates_removed'], 7)
        self.assertAlmostEqual(first['energy'], second['energy'], places=8)
        np.testing.assert_allclose(
            [[a[k] for k in ('x', 'y', 'z')] for a in first['atoms']],
            [[a[k] for k in ('x', 'y', 'z')] for a in second['atoms']], atol=1e-8)

    def test_search_rejects_unsupported_method_and_unbounded_inputs(self):
        molecule = prepare_molecule('CCCC', 'smiles', 'Butane')
        for changes in ({'method':'GFN2-xTB'}, {'conformer_count':0},
                        {'conformer_count':101}, {'conformer_count':2.5},
                        {'rmsd_threshold':float('nan')}, {'rmsd_threshold':0},
                        {'frequencies':True}, {'solvent':'water'}):
            settings = self.settings()
            settings.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_settings(molecule, settings)


if __name__ == '__main__':
    unittest.main()
