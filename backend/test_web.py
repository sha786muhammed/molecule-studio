"""Public behavior of the loopback server used by the local launcher."""
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend import storage


class LocalWebTests(unittest.TestCase):
    def setUp(self):
        from backend.web import create_local_app
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.frontend = self.root / 'client'
        (self.frontend / 'assets').mkdir(parents=True)
        (self.frontend / 'index.html').write_text('<html><title>Local workbench</title></html>')
        (self.frontend / 'assets' / 'app.js').write_text('export const ready = true;')
        (self.root / 'private.txt').write_text('private scientific data')
        self.old_database = storage.DB
        storage.DB = self.root / 'studio.sqlite3'
        self.client = TestClient(create_local_app(self.frontend))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB = self.old_database
        self.directory.cleanup()

    def test_serves_the_built_frontend_and_real_api_together(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Local workbench', response.text)
        self.assertEqual(self.client.get('/assets/app.js').text, 'export const ready = true;')
        self.assertEqual(self.client.get('/api/health').json()['status'], 'ready')
        self.assertGreater(len(self.client.get('/api/molecules').json()), 0)

    def test_missing_api_and_repository_files_are_not_frontend_pages(self):
        for route in ('/api/not-an-endpoint', '/private.txt', '/requirements.txt',
                      '/%2e%2e/private.txt', '/assets/missing.js'):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn('Local workbench', response.text)
                self.assertNotIn('private scientific data', response.text)
        self.assertNotEqual(self.client.post('/not-an-endpoint', json={}).status_code, 200)

    def test_missing_build_has_a_clear_setup_error(self):
        from backend.web import create_local_app
        with self.assertRaisesRegex(RuntimeError, 'build'):
            create_local_app(self.root / 'not-built')


if __name__ == '__main__':
    unittest.main()
