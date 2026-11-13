import os
os.environ['OMP_NUM_THREADS']='1'
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from threading import BoundedSemaphore
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
import json, re
from pydantic import BaseModel, Field
from typing import Literal
from backend import storage as store
from backend.chemistry import prepare_molecule,run_calculation,validate_settings
app=FastAPI(title='Molecule Studio API',version='0.1.0')
pool=ThreadPoolExecutor(max_workers=1)
demo_slots=BoundedSemaphore(3)
def is_demo(): return os.environ.get('STUDIO_DEMO')=='1'
@app.on_event('startup')
def startup():
    if not is_demo(): initialize_workspace()
def initialize_workspace():
    store.init()
    for j in store.all_records('job'):
        if j['status'] in ('running','queued'): j.update(status='interrupted',error='The calculation service restarted. Submit again.'); store.save('job',j)
    if not store.all_records('project'):
        p=store.save('project',{'name':'Small molecules','description':'Your molecular workbench. Draw, calculate, and explore.'})
        for name,smiles in [('Caffeine','Cn1c(=O)c2c(ncn2C)n(C)c1=O'),('Ethanol','CCO'),('Water','O'),('Aspirin','CC(=O)Oc1ccccc1C(=O)O')]:
            m=prepare_molecule(smiles,'smiles',name); m['project_id']=p['id']; store.save('molecule',m)
@app.get('/api/health')
def health():
    import rdkit,importlib.metadata
    return {'status':'ready','engines':{'RDKit':rdkit.__version__,'tblite':importlib.metadata.version('tblite'),'ASE':importlib.metadata.version('ase')},'demo':is_demo(),'scope':'Temporary browser workspace' if is_demo() else 'Local single-user application','limits':{'atoms':40 if is_demo() else 80,'frequency_atoms':9 if is_demo() else 18,'conformers':30 if is_demo() else 100}}
class ProjectInput(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    description:str=Field(default='',max_length=1000)
@app.get('/api/projects')
def projects(): return store.all_records('project')
@app.post('/api/projects')
def add_project(body:ProjectInput):
    with store.LOCK:
        if is_demo() and len(store.all_records('project'))>=5: raise HTTPException(429,'Demo limit: five projects per browser workspace.')
        return store.save('project',body.model_dump())
class MoleculeInput(BaseModel):
    name:str=Field(default='Untitled molecule',max_length=120)
    content:str=Field(min_length=1,max_length=1_000_000)
    kind:Literal['smiles','mol','sdf','xyz']='smiles'
    project_id:str
@app.get('/api/molecules')
def molecules(): return store.all_records('molecule')
@app.post('/api/molecules')
def add_molecule(body:MoleculeInput):
    if not store.get(body.project_id): raise HTTPException(400,'Choose a valid project.')
    try: m=prepare_molecule(body.content,body.kind,body.name)
    except (ValueError,RuntimeError) as e: raise HTTPException(400,str(e))
    if is_demo() and len(m['atoms'])>40: raise HTTPException(400,'Free demo: up to 40 atoms including hydrogen. Run locally for larger structures.')
    m['project_id']=body.project_id
    with store.LOCK:
        if is_demo() and len(store.all_records('molecule'))>=20: raise HTTPException(429,'Demo limit: 20 molecules per browser workspace. Download your work or run locally.')
        return store.save('molecule',m)
class JobInput(BaseModel):
    molecule_id:str
    name:str=Field(default='',max_length=120)
    method:Literal['GFN2-xTB','MMFF94','UFF']='GFN2-xTB'
    task:Literal['optimize','singlepoint','conformers']='optimize'
    charge:int=Field(default=0,ge=-5,le=5)
    multiplicity:int=Field(default=1,ge=1,le=5)
    solvent:Literal['gas','water','ethanol','acetonitrile']='gas'
    frequencies:bool=False
    conformer_count:int=Field(default=30,ge=1,le=100)
    rmsd_threshold:float=Field(default=0.5,ge=0.1,le=2,allow_inf_nan=False)
@app.get('/api/jobs')
def jobs(): return [{k:v for k,v in j.items() if k!='result'} for j in store.all_records('job')]
@app.get('/api/jobs/{identifier}')
def job(identifier:str):
    j=store.get(identifier)
    if not j or 'status' not in j: raise HTTPException(404,'Calculation not found.')
    return j

@app.get('/api/jobs/{identifier}/export/{format}')
def export_job(identifier:str,format:Literal['xyz','sdf','json'],conformer:int|None=Query(default=None,ge=1)):
    j=job(identifier)
    if not j.get('result'): raise HTTPException(400,'This calculation has no result to export.')
    r=j['result'];name=re.sub(r'[^A-Za-z0-9_-]+','-',j['molecule']['name']).strip('-') or 'molecule'
    structures=r.get('conformers',[r])
    if conformer is not None:
        if not r.get('conformers') or conformer>len(structures): raise HTTPException(400,'Choose a conformer from this result.')
        structures=[structures[conformer-1]];name+=f'-conformer-{conformer}'
    if format=='json': content=json.dumps(j,indent=2)
    elif format=='xyz': content=''.join(c['xyz'] for c in structures)
    else:
        from rdkit import Chem
        import io
        buffer=io.StringIO()
        writer=Chem.SDWriter(buffer)
        for structure in structures:
            mol=Chem.MolFromMolBlock(structure['molblock'],removeHs=False)
            mol.SetProp('_Name',j['molecule']['name']+(f' conformer {structure["rank"]}' if r.get('conformers') else ''))
            mol.SetProp('Method',r['method'])
            mol.SetProp('Energy',str(structure['energy']))
            mol.SetProp('Energy_unit',r['energy_unit'])
            if r.get('conformers'):
                mol.SetProp('Relative_energy_kcal_mol',str(structure['relative_energy']))
                mol.SetProp('Conformer_rank',str(structure['rank']))
                mol.SetProp('Sampling_seed',str(r['search']['seed']))
            writer.write(mol)
        writer.flush();content=buffer.getvalue();writer.close()
    return Response(content,media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="{name}.{format}"'})
def execute(identifier):
    j=store.get(identifier); j['status']='running'; store.save('job',j)
    try:
        def progress(step,energy,unit): j.update(step=step,current_energy=energy,energy_unit=unit); store.save('job',j)
        r=run_calculation(j['molecule'],j['settings'],progress); j.update(result=r,status='completed' if r['converged'] else 'unconverged')
    except Exception as e: j.update(status='failed',error=str(e))
    store.save('job',j)
@app.post('/api/jobs')
def add_job(body:JobInput):
    mol=store.get(body.molecule_id)
    if not mol or 'molblock' not in mol: raise HTTPException(404,'Molecule not found.')
    settings=body.model_dump(exclude={'name','molecule_id'})
    try: validate_settings(mol,settings)
    except ValueError as e: raise HTTPException(400,str(e))
    if is_demo():
        if len(mol['atoms'])>40 or (body.frequencies and len(mol['atoms'])>9) or (body.task=='conformers' and body.conformer_count>30):
            raise HTTPException(400,'Free demo: 40 atoms, 9 atoms for frequencies, and 30 conformer candidates. Run locally for larger calculations.')
    with store.LOCK:
        existing=store.all_records('job')
        active=sum(j['status'] in ('queued','running') for j in existing)
        if active>=(1 if is_demo() else 5): raise HTTPException(429,'Wait for your active calculation to finish.')
        if is_demo() and len(existing)>=10: raise HTTPException(429,'Demo limit: ten calculations per browser workspace. Download your results or run locally.')
        reserved=is_demo()
        if reserved and not demo_slots.acquire(blocking=False): raise HTTPException(429,'The free demo is busy. Please try again after a calculation finishes.')
        try:
            j=store.save('job',{'name':body.name or mol['name']+' · '+body.method+(' · conformers' if body.task=='conformers' else ''),'molecule':mol,'project_id':mol['project_id'],'settings':settings,'status':'queued','step':0})
            future=pool.submit(copy_context().run,execute,j['id'])
        except BaseException:
            if reserved: demo_slots.release()
            raise
        if reserved: future.add_done_callback(lambda _: demo_slots.release())
        return j
