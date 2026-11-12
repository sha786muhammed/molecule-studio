import io,tempfile,time,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend import storage
from backend.app import app
from rdkit import Chem

class ApiTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=storage.DB;storage.DB=Path(self.tmp.name)/'studio.sqlite3';self.client=TestClient(app);self.client.__enter__()
 def tearDown(self):
  self.client.__exit__(None,None,None);storage.DB=self.old;self.tmp.cleanup()
 def test_saved_project_molecule_and_real_job_workflow(self):
  p=self.client.post('/api/projects',json={'name':'Validation','description':'API integration'}).json()
  m=self.client.post('/api/molecules',json={'name':'Test water','content':'O','kind':'smiles','project_id':p['id']}).json()
  self.assertEqual(m['formula'],'H2O')
  response=self.client.post('/api/jobs',json={'molecule_id':m['id'],'method':'GFN2-xTB','task':'singlepoint','charge':0,'multiplicity':1})
  self.assertEqual(response.status_code,200);j=response.json()
  for _ in range(100):
   j=self.client.get('/api/jobs/'+j['id']).json()
   if j['status'] not in ('running','queued'):break
   time.sleep(.05)
  self.assertEqual(j['status'],'completed',j.get('error'))
  self.assertTrue(j['result']['energy']<0)
  self.assertEqual(storage.get(m['id'])['name'],'Test water')
  exported=self.client.get('/api/jobs/'+j['id']+'/export/xyz')
  self.assertEqual(exported.status_code,200)
  self.assertEqual(exported.text.splitlines()[0],'3')
  self.assertIn('attachment',exported.headers['content-disposition'])
 def test_invalid_input_and_unknown_job(self):
  pid=self.client.get('/api/projects').json()[0]['id']
  r=self.client.post('/api/molecules',json={'name':'Bad','content':'not smiles','kind':'smiles','project_id':pid})
  self.assertEqual(r.status_code,400)
  self.assertEqual(self.client.get('/api/jobs/no-such-id').status_code,404)
 def test_conformer_job_persists_and_exports_the_ensemble(self):
  pid=self.client.get('/api/projects').json()[0]['id']
  m=self.client.post('/api/molecules',json={'name':'Butane','content':'CCCC','kind':'smiles','project_id':pid}).json()
  response=self.client.post('/api/jobs',json={'molecule_id':m['id'],'method':'MMFF94','task':'conformers','conformer_count':30,'rmsd_threshold':0.5})
  self.assertEqual(response.status_code,200,response.text)
  identifier=response.json()['id']
  for _ in range(100):
   j=self.client.get('/api/jobs/'+identifier).json()
   if j['status'] not in ('running','queued'):break
   time.sleep(.05)
  self.assertEqual(j['status'],'completed',j.get('error'))
  count=len(j['result']['conformers'])
  self.assertGreaterEqual(count,2)
  self.assertEqual(storage.get(identifier)['result']['search']['unique'],count)
  prefix='/api/jobs/'+identifier+'/export/'
  xyz=self.client.get(prefix+'xyz')
  self.assertEqual(len(xyz.text.splitlines()),count*16)  # C4H10 plus two XYZ header lines.
  exported=self.client.get(prefix+'sdf')
  records=list(Chem.ForwardSDMolSupplier(io.BytesIO(exported.content),removeHs=False))
  self.assertEqual(len(records),count)
  self.assertTrue(all(record is not None for record in records))
  self.assertEqual(records[0].GetProp('Method'),'MMFF94')
  self.assertAlmostEqual(float(records[0].GetProp('Relative_energy_kcal_mol')),0,places=8)
  selected=self.client.get(prefix+'xyz?conformer=2')
  self.assertEqual(selected.text,j['result']['conformers'][1]['xyz'])
  self.assertIn('conformer-2',selected.headers['content-disposition'])
  self.assertEqual(self.client.get(prefix+'xyz?conformer=999').status_code,400)
 def test_invalid_conformer_settings_rejected_before_queue(self):
  mid=self.client.get('/api/molecules').json()[0]['id']
  for change in ({'method':'GFN2-xTB'},{'conformer_count':101},{'rmsd_threshold':0}):
   payload={'molecule_id':mid,'task':'conformers','method':'MMFF94',**change}
   r=self.client.post('/api/jobs',json=payload)
   self.assertIn(r.status_code,(400,422))
  self.assertEqual(self.client.get('/api/jobs').json(),[])

if __name__=='__main__':unittest.main()
