"""Scientific operations. Coordinates in angstrom unless explicitly converted."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import tempfile, time
import numpy as np
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, Descriptors, Crippen, rdMolDescriptors, Draw, rdDetermineBonds

def coordinates(mol):
    p = mol.GetConformer().GetPositions()
    return [{'element':a.GetSymbol(), 'number':a.GetAtomicNum(), 'x':float(p[i,0]), 'y':float(p[i,1]), 'z':float(p[i,2])} for i,a in enumerate(mol.GetAtoms())]

def xyz_text(atoms, comment='Molecule Studio; coordinates in angstrom'):
    return f'{len(atoms)}\n{comment}\n' + '\n'.join(f"{a['element']} {a['x']:.10f} {a['y']:.10f} {a['z']:.10f}" for a in atoms) + '\n'

def prepare_molecule(content, kind='smiles', name='Untitled molecule'):
    if len(content)>1_000_000: raise ValueError('Structure file must be smaller than 1 MB.')
    if kind=='smiles': mol=Chem.MolFromSmiles(content.strip())
    elif kind in ('mol','sdf'): mol=Chem.MolFromMolBlock(content.split('$$$$')[0],removeHs=False)
    elif kind=='xyz':
        mol=Chem.MolFromXYZBlock(content)
        if mol is not None:
            try: rdDetermineBonds.DetermineBonds(mol,charge=0)
            except Exception: raise ValueError('Could not infer bonds from XYZ. Use MOL/SDF for charged or unusual structures.')
    else: raise ValueError('Use SMILES, MOL, SDF, or XYZ input.')
    if mol is None or not mol.GetNumAtoms(): raise ValueError('Could not read the structure. Check the SMILES or upload a valid molecular file.')
    if len(Chem.GetMolFrags(mol))!=1: raise ValueError('Use one connected molecule per calculation. Separate salts and fragments first.')
    smiles=Chem.MolToSmiles(Chem.RemoveHs(mol)); charge=Chem.GetFormalCharge(mol)
    d={'mw':Descriptors.MolWt(mol),'logp':Crippen.MolLogP(mol),'tpsa':rdMolDescriptors.CalcTPSA(mol),'hbd':rdMolDescriptors.CalcNumHBD(mol),'hba':rdMolDescriptors.CalcNumHBA(mol),'rotatable':rdMolDescriptors.CalcNumRotatableBonds(mol),'rings':rdMolDescriptors.CalcNumRings(mol),'heavy_atoms':mol.GetNumHeavyAtoms()}
    formula=rdMolDescriptors.CalcMolFormula(mol)
    depict=Chem.RemoveHs(Chem.Mol(mol)); AllChem.Compute2DCoords(depict)
    drawer=Draw.rdMolDraw2D.MolDraw2DSVG(600,420); drawer.DrawMolecule(depict); drawer.FinishDrawing()
    mol=Chem.AddHs(mol,addCoords=True)
    if mol.GetNumAtoms()>80: raise ValueError('This local version supports up to 80 atoms including hydrogens.')
    if kind=='smiles' or not mol.GetNumConformers() or not mol.GetConformer().Is3D():
        params=AllChem.ETKDGv3(); params.randomSeed=42
        if AllChem.EmbedMolecule(mol,params)!=0: raise ValueError('3D generation failed. Import a valid 3D MOL/SDF structure.')
    atoms=coordinates(mol)
    return {'name':name.strip()[:120] or 'Untitled molecule','smiles':smiles,'formula':formula,'formal_charge':charge,'descriptors':d,'atoms':atoms,'xyz':xyz_text(atoms),'molblock':Chem.MolToMolBlock(mol),'svg':drawer.GetDrawingText(),'preparation':'RDKit ETKDGv3' if kind=='smiles' else 'Imported coordinates / RDKit preparation','rdkit_version':rdBase.rdkitVersion}

def validate_settings(molecule,s):
    method=s.get('method','GFN2-xTB'); charge=int(s.get('charge',0)); mult=int(s.get('multiplicity',1))
    if method not in ['GFN2-xTB','MMFF94','UFF']: raise ValueError('Select GFN2-xTB, MMFF94, or UFF.')
    if s.get('task') not in ('optimize','singlepoint','conformers'): raise ValueError('Select optimization, single-point energy, or conformer search.')
    if s.get('task')=='conformers':
        if method not in ('MMFF94','UFF'): raise ValueError('Conformer search supports MMFF94 or UFF. Refine selected structures with xTB afterward.')
        count=s.get('conformer_count',30); rmsd=s.get('rmsd_threshold',0.5)
        if isinstance(count,bool) or not isinstance(count,int) or not 1<=count<=100: raise ValueError('Request between 1 and 100 candidate conformers.')
        if not isinstance(rmsd,(int,float)) or not np.isfinite(rmsd) or not 0.1<=rmsd<=2: raise ValueError('The RMSD threshold must be between 0.1 and 2 Å.')
    if charge!=molecule['formal_charge']: raise ValueError('Charge must match the drawn structure. Edit the formal charge or use a charged SMILES.')
    ne=sum(a['number'] for a in molecule['atoms'])-charge
    if mult<1 or mult>5 or (ne-(mult-1))%2: raise ValueError('Multiplicity is inconsistent with the electron count. Even electron counts require odd multiplicity; odd counts require even multiplicity.')
    if s.get('solvent','gas') not in ('gas','water','ethanol','acetonitrile'): raise ValueError('Unsupported solvent.')
    if method!='GFN2-xTB' and (s.get('solvent','gas')!='gas' or mult!=1): raise ValueError('Force-field calculations support gas phase and closed-shell structures only.')
    if s.get('frequencies'):
        if method!='GFN2-xTB' or s.get('task')!='optimize': raise ValueError('Frequencies require a GFN2-xTB geometry optimization.')
        if len(molecule['atoms'])>18: raise ValueError('Numerical frequencies are limited to 18 atoms including hydrogens.')

def internal_vibrations(data, atoms):
    """Project rigid translation/rotation out of the mass-weighted Hessian."""
    from ase import units
    masses=atoms.get_masses(); root=np.sqrt(masses)[:,None]
    centered=atoms.positions-atoms.get_center_of_mass()
    rigid=[]
    for axis in np.eye(3):
        rigid.append((np.tile(axis,(len(atoms),1))*root).ravel())
        rigid.append((np.cross(axis,centered)*root).ravel())
    u,s,_=np.linalg.svd(np.asarray(rigid).T,full_matrices=True)
    rank=int(np.sum(s>s[0]*1e-8)); basis=u[:,rank:]
    weights=np.repeat(1/np.sqrt(masses),3)
    dynamical=data.get_hessian_2d()*np.outer(weights,weights)
    projected=basis.T@dynamical@basis
    eigenvalues,eigenvectors=np.linalg.eigh((projected+projected.T)/2)
    conversion=units._hbar*units.m/np.sqrt(units._e*units._amu)/units.invcm
    wavenumbers=np.sign(eigenvalues)*np.sqrt(np.abs(eigenvalues))*conversion
    modes=[((basis@eigenvectors[:,i]).reshape(-1,3)/root).tolist() for i in range(len(eigenvalues))]
    return [{'mode':i+1,'wavenumber':float(v),'imaginary':bool(v<0)} for i,v in enumerate(wavenumbers)],modes

def run_calculation(molecule,settings,progress=None):
    validate_settings(molecule,settings)
    if settings['task']=='conformers':
        from backend.conformers import search_conformers
        return search_conformers(molecule,settings,progress)
    started=time.time(); method=settings['method']; mol=Chem.MolFromMolBlock(molecule['molblock'],removeHs=False)
    history=[]; frequencies=None; modes=None; charges=None; dipole=None; orbitals=None
    def report(step,energy,unit):
        history.append({'step':step,'energy':float(energy),'unit':unit})
        if progress: progress(step,float(energy),unit)
    if method in ('MMFF94','UFF'):
        if method=='MMFF94':
            if not AllChem.MMFFHasAllMoleculeParams(mol): raise ValueError('MMFF94 parameters are missing. Try UFF or GFN2-xTB.')
            ff=AllChem.MMFFGetMoleculeForceField(mol,AllChem.MMFFGetMoleculeProperties(mol))
        else:
            if not AllChem.UFFHasAllMoleculeParams(mol): raise ValueError('UFF parameters are missing for this molecule.')
            ff=AllChem.UFFGetMoleculeForceField(mol)
        initial=float(ff.CalcEnergy()); report(0,initial,'kcal/mol'); converged=True
        if settings['task']=='optimize':
            converged=False
            for step in range(1,101):
                status=ff.Minimize(maxIts=10,forceTol=1e-4,energyTol=1e-8); report(step*10,ff.CalcEnergy(),'kcal/mol')
                if status==0: converged=True; break
        energy=float(ff.CalcEnergy()); unit='kcal/mol'; engine=f'RDKit {rdBase.rdkitVersion}'; grad=None
    else:
        from ase import Atoms
        from ase.optimize import BFGS
        from tblite.ase import TBLite
        from ase.units import Hartree
        import importlib.metadata
        a=Atoms(numbers=[x['number'] for x in molecule['atoms']],positions=[[x['x'],x['y'],x['z']] for x in molecule['atoms']])
        params={'method':'GFN2-xTB','charge':int(settings['charge']),'multiplicity':int(settings['multiplicity']),'verbosity':0}
        if settings.get('solvent','gas')!='gas': params['solvation']=('alpb',settings['solvent'])
        a.calc=TBLite(**params)
        initial=float(a.get_potential_energy()/Hartree); report(0,initial,'Hartree'); converged=True
        if settings['task']=='optimize':
            opt=BFGS(a,logfile=None,maxstep=0.15)
            opt.attach(lambda:report(opt.nsteps,a.get_potential_energy()/Hartree,'Hartree'),interval=1)
            converged=bool(opt.run(fmax=0.03,steps=180))
        energy=float(a.get_potential_energy()/Hartree); unit='Hartree'; grad=float(np.max(np.linalg.norm(a.get_forces(),axis=1)))
        for i,p in enumerate(a.positions): mol.GetConformer().SetAtomPosition(i,p.tolist())
        charges=np.asarray(a.get_charges()).tolist(); dipole=float(np.linalg.norm(a.get_dipole_moment())/0.20819433442462576)
        try:
            raw=a.calc._res; es=np.asarray(raw.get('orbital-energies')).reshape(-1)*Hartree; occ=np.asarray(raw.get('orbital-occupations')).reshape(-1)
            occupied=es[occ>0.1]; virtual=es[occ<0.1]
            if len(occupied) and len(virtual): orbitals={'homo':float(max(occupied)),'lumo':float(min(virtual)),'gap':float(min(virtual)-max(occupied)),'unit':'eV','model':'GFN2-xTB orbital energies (not a DFT or optical gap)'}
        except (AttributeError,KeyError,RuntimeError): pass
        if settings.get('frequencies'):
            if not converged: raise ValueError('Optimization did not converge. Frequencies were not calculated.')
            from ase.vibrations import Vibrations
            with tempfile.TemporaryDirectory() as tmp:
                vib=Vibrations(a,name=tmp+'/vib',delta=0.01,nfree=2); vib.run()
                frequencies,modes=internal_vibrations(vib.get_vibrations(),a)
        engine='tblite '+importlib.metadata.version('tblite')+' / ASE '+importlib.metadata.version('ase')
    atoms=coordinates(mol)
    notes=['Gas-phase isolated molecule.' if settings.get('solvent','gas')=='gas' else 'ALPB implicit solvation: '+settings['solvent']+'.']
    notes.append('Force-field energy is not an electronic energy; dipole and quantum charges are not computed.' if method!='GFN2-xTB' else 'GFN2-xTB is a semiempirical tight-binding method, not DFT. Atomic charges are model dependent.')
    if int(settings.get('charge',0))!=0: notes.append('Dipole of a charged molecule depends on the coordinate origin.')
    if frequencies: notes.append('Mass-weighted rigid translations/rotations are projected out. Inspect imaginary internal modes. No thermochemical corrections or IR intensities are calculated.')
    return {'method':method,'task':settings['task'],'energy':energy,'initial_energy':initial,'energy_unit':unit,'converged':converged,'max_force_ev_angstrom':grad,'dipole':dipole,'dipole_unit':'Debye','charges':charges,'charge_model':'GFN2-xTB Mulliken' if charges is not None else None,'orbitals':orbitals,'frequencies':frequencies,'frequency_projection':'mass-weighted Eckart rigid-body projection' if frequencies else None,'modes':modes,'atoms':atoms,'xyz':xyz_text(atoms,f'{molecule["name"]}; {method}; {energy:.10f} {unit}'),'molblock':Chem.MolToMolBlock(mol),'history':history,'engine':engine,'duration':round(time.time()-started,2),'notes':notes,'settings':settings,'coordinate_unit':'angstrom'}
