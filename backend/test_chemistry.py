import unittest
import numpy as np
from backend.chemistry import prepare_molecule, run_calculation

class ChemistryTests(unittest.TestCase):
    def test_ethanol_descriptors_and_explicit_hydrogens(self):
        m = prepare_molecule('CCO', 'smiles', 'Ethanol')
        self.assertEqual(m['formula'], 'C2H6O')
        self.assertAlmostEqual(m['descriptors']['mw'], 46.069, places=2)
        self.assertEqual(len(m['atoms']), 9)
        self.assertEqual(m['descriptors']['hbd'], 1)

    def test_invalid_smiles_is_rejected(self):
        with self.assertRaises(ValueError): prepare_molecule('not a molecule', 'smiles', 'Invalid')

    def test_forcefield_optimization_lowers_energy(self):
        m = prepare_molecule('CCO', 'smiles', 'Ethanol')
        r = run_calculation(m, {'method':'MMFF94', 'task':'optimize', 'charge':0, 'multiplicity':1, 'solvent':'gas', 'frequencies':False})
        self.assertTrue(r['converged'])
        self.assertLessEqual(r['energy'], r['initial_energy'] + 1e-7)
        self.assertEqual(r['energy_unit'], 'kcal/mol')
        self.assertIsNone(r['dipole'])

    def test_quantum_water_charge_and_dipole(self):
        m = prepare_molecule('O', 'smiles', 'Water')
        r = run_calculation(m, {'method':'GFN2-xTB', 'task':'singlepoint', 'charge':0, 'multiplicity':1, 'solvent':'gas', 'frequencies':False})
        self.assertEqual(r['energy_unit'], 'Hartree')
        self.assertAlmostEqual(sum(r['charges']), 0, places=5)
        self.assertGreater(r['dipole'], 0.5)
        self.assertLess(r['dipole'], 4)
        self.assertTrue(np.isfinite(r['energy']))

    def test_inconsistent_spin_is_rejected(self):
        m = prepare_molecule('O', 'smiles', 'Water')
        with self.assertRaises(ValueError):
            run_calculation(m, {'method':'GFN2-xTB', 'task':'singlepoint', 'charge':0, 'multiplicity':2, 'solvent':'gas', 'frequencies':False})

    def test_water_frequencies_exclude_rigid_motion(self):
        m=prepare_molecule('O','smiles','Water')
        r=run_calculation(m,{'method':'GFN2-xTB','task':'optimize','charge':0,'multiplicity':1,'solvent':'gas','frequencies':True})
        self.assertEqual(len(r['frequencies']),3)
        self.assertTrue(all(f['wavenumber']>1000 for f in r['frequencies']))

if __name__ == '__main__': unittest.main()
