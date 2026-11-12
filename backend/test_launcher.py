"""Test prerequisite failures without touching the user's Python environment."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[1] / 'launch.py'


class LauncherTests(unittest.TestCase):
    def test_missing_node_is_reported_before_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, PATH=directory)
            result = subprocess.run([sys.executable, str(LAUNCHER), '--check'],
                                    cwd=directory, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Node.js 22', result.stderr)
            self.assertFalse((Path(directory) / '.venv').exists())

    def test_prerequisite_check_works_outside_project_without_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / 'launch.py'
            if LAUNCHER.exists():
                shutil.copyfile(LAUNCHER, script)
            result = subprocess.run([sys.executable, str(script), '--check'],
                                    cwd=Path(directory).parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Prerequisites ready', result.stdout)
            self.assertFalse((Path(directory) / '.venv').exists())


if __name__ == '__main__':
    unittest.main()
