"""The public demo must not expose another browser's structures or jobs."""
import tempfile
import time
import unittest
from contextlib import ExitStack
from threading import Event
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import storage


class HostedTests(unittest.TestCase):
    def setUp(self):
        from backend.hosted import create_hosted_app
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.frontend = self.root / 'client'
        self.frontend.mkdir()
        (self.frontend / 'index.html').write_text('<html>Hosted workbench</html>')
        self.old_database = storage.DB
        storage.DB = self.root / 'studio.sqlite3'
        self.environment = patch.dict('os.environ', {'STUDIO_DEMO': '1'})
        self.environment.start()
        application = create_hosted_app(self.frontend)
        self.alice = TestClient(application, base_url='https://demo.test')
        self.bob = TestClient(application, base_url='https://demo.test')
        self.alice.__enter__()
        self.bob.__enter__()

    def tearDown(self):
        self.alice.__exit__(None, None, None)
        self.bob.__exit__(None, None, None)
        self.environment.stop()
        storage.DB = self.old_database
        self.directory.cleanup()

    def test_two_browsers_have_separate_projects_and_molecules(self):
        storage.init()
        storage.save('project', {'name': 'Local unpublished research'})
        page = self.alice.get('/')
        self.assertIn('Hosted workbench', page.text)
        self.assertIn('HttpOnly', page.headers['set-cookie'])
        self.assertIn('Secure', page.headers['set-cookie'])
        self.assertNotIn('Local unpublished research', [p['name'] for p in self.alice.get('/api/projects').json()])
        p = self.alice.post('/api/projects', json={'name': 'Alice research'}).json()
        self.assertNotIn(p['id'], [p['id'] for p in self.bob.get('/api/projects').json()])
        payload = {'name': 'Hidden molecule', 'content': 'O', 'project_id': p['id']}
        self.assertEqual(self.bob.post('/api/molecules', json=payload).status_code, 400)
        self.assertEqual(self.alice.post('/api/molecules', json=payload).status_code, 200)
        self.assertNotIn('Hidden molecule', [m['name'] for m in self.bob.get('/api/molecules').json()])

    def test_real_background_job_and_export_stay_in_the_owners_workspace(self):
        mid = next(m['id'] for m in self.alice.get('/api/molecules').json() if m['name'] == 'Water')
        response = self.alice.post('/api/jobs', json={'molecule_id': mid, 'method': 'GFN2-xTB', 'task': 'singlepoint'})
        self.assertEqual(response.status_code, 200, response.text)
        identifier = response.json()['id']
        for _ in range(200):
            j = self.alice.get('/api/jobs/' + identifier).json()
            if j['status'] not in ('queued', 'running'):
                break
            time.sleep(.025)
        self.assertEqual(j['status'], 'completed', j)
        self.assertLess(j['result']['energy'], 0)
        path = '/api/jobs/' + identifier
        self.assertEqual(self.alice.get(path + '/export/xyz').text.splitlines()[0], '3')
        self.assertEqual(self.bob.get(path).status_code, 404)
        self.assertEqual(self.bob.get(path + '/export/json').status_code, 404)
        self.assertEqual(self.bob.post('/api/jobs', json={'molecule_id': mid}).status_code, 404)

    def test_tampered_cookie_cannot_reopen_a_workspace(self):
        self.alice.post('/api/projects', json={'name': 'Private project'})
        cookie = self.alice.cookies.get('studio_session')
        self.bob.cookies.set('studio_session', cookie[:-1] + ('0' if cookie[-1] != '0' else '1'))
        self.assertNotIn('Private project', [p['name'] for p in self.bob.get('/api/projects').json()])

    def test_demo_limits_and_cross_origin_writes(self):
        health = self.alice.get('/api/health').json()
        self.assertTrue(health['demo'])
        mid = self.alice.get('/api/molecules').json()[0]['id']
        r = self.alice.post('/api/jobs', json={'molecule_id': mid, 'method': 'MMFF94', 'task': 'conformers', 'conformer_count': 100})
        self.assertEqual(r.status_code, 400)
        r = self.alice.post('/api/projects', json={'name': 'External'}, headers={'Origin': 'https://other.test'})
        self.assertEqual(r.status_code, 403)
        for i in range(4):
            self.assertEqual(self.alice.post('/api/projects', json={'name': str(i)}).status_code, 200)
        self.assertEqual(self.alice.post('/api/projects', json={'name': 'Over limit'}).status_code, 429)

    def test_expired_cookie_starts_a_new_workspace(self):
        self.alice.post('/api/projects', json={'name': 'Yesterday research'})
        tomorrow = time.time() + 90000
        with patch('backend.hosted.time.time', return_value=tomorrow):
            projects = self.alice.get('/api/projects').json()
        self.assertNotIn('Yesterday research', [p['name'] for p in projects])

    def test_global_queue_is_bounded_across_visitors(self):
        from backend.app import pool
        release, started = Event(), Event()
        def hold_worker():
            started.set()
            release.wait(10)
        pool.submit(hold_worker)
        self.assertTrue(started.wait(2))
        try:
            with ExitStack() as stack:
                clients = [self.alice, self.bob] + [stack.enter_context(TestClient(self.alice.app, base_url='https://demo.test')) for _ in range(2)]
                for index, client in enumerate(clients):
                    mid = next(m['id'] for m in client.get('/api/molecules').json() if m['name'] == 'Water')
                    payload = {'molecule_id': mid, 'method': 'GFN2-xTB', 'task': 'singlepoint'}
                    r = client.post('/api/jobs', json=payload)
                    self.assertEqual(r.status_code, 200 if index < 3 else 429, r.text)
                    if index == 0:
                        self.assertEqual(client.post('/api/jobs', json=payload).status_code, 429)
        finally:
            release.set()
            pool.submit(lambda: None).result(timeout=10)


if __name__ == '__main__':
    unittest.main()
