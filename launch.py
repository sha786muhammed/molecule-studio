#!/usr/bin/env python3
"""Install and launch Molecule Studio locally using Python 3.12+ and Node.js 22+."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
ENVIRONMENT = ROOT / '.venv'


def prerequisites():
    if sys.version_info < (3, 12):
        raise RuntimeError('Python 3.12 or newer is required. Install it from https://www.python.org/downloads/.')
    node = shutil.which('node')
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not node or not npm:
        raise RuntimeError('Node.js 22 or newer with npm is required. Install the LTS release from https://nodejs.org/.')
    try:
        version = subprocess.check_output([node, '--version'], text=True, stderr=subprocess.STDOUT).strip()
        if int(version.lstrip('v').split('.')[0]) < 22:
            raise ValueError(version)
    except (subprocess.CalledProcessError, ValueError) as exc:
        raise RuntimeError('Node.js 22 or newer is required. Update Node.js from https://nodejs.org/.') from exc
    print(f'Prerequisites ready: Python {sys.version.split()[0]}, Node.js {version}', flush=True)
    return npm


def install(npm, environment):
    python = ENVIRONMENT / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        print('Creating a separate Python environment in .venv…', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(ENVIRONMENT)], cwd=ROOT, env=environment, check=True)
    requirements = hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest()
    python_marker = ENVIRONMENT / 'studio-requirements.sha256'
    if not python_marker.exists() or python_marker.read_text().strip() != requirements:
        print('Installing scientific packages. The first run needs an internet connection…', flush=True)
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], cwd=ROOT, env=environment, check=True)
        python_marker.write_text(requirements)
    lock = hashlib.sha256((ROOT / 'package-lock.json').read_bytes()).hexdigest()
    node_marker = ENVIRONMENT / 'studio-node-lock.sha256'
    if not (ROOT / 'node_modules').is_dir() or not node_marker.exists() or node_marker.read_text().strip() != lock:
        print('Installing interface packages…', flush=True)
        subprocess.run([npm, 'ci'], cwd=ROOT, env=environment, check=True)
        node_marker.write_text(lock)
    print('Building the browser interface…', flush=True)
    subprocess.run([npm, 'run', 'build'], cwd=ROOT, env=environment, check=True)
    return python


def serve(python, port, environment, open_browser):
    url = f'http://127.0.0.1:{port}'
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', port))
        except OSError as exc:
            raise RuntimeError(f'Port {port} is already in use. Retry with --port {port + 1 if port < 65535 else 8765}.') from exc
    process = subprocess.Popen([str(python), '-m', 'backend.web', '--port', str(port)], cwd=ROOT, env=environment)
    try:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('The calculation server stopped during startup. Check the error above.')
            try:
                with urllib.request.urlopen(url + '/api/health', timeout=2) as response:
                    if json.load(response).get('status') == 'ready':
                        break
            except (urllib.error.URLError, TimeoutError, ValueError):
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError('The calculation engine did not become ready within 45 seconds.')
        print(f'\nMolecule Studio is ready. Open {url}\nKeep this terminal open. Press Ctrl+C to stop; your saved projects remain on disk.\n', flush=True)
        if open_browser:
            try:
                webbrowser.open(url)
            except webbrowser.Error:
                print('Open the address above in your browser.', flush=True)
        return process.wait()
    except KeyboardInterrupt:
        print('\nStopping Molecule Studio…', flush=True)
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check prerequisites without installing anything.')
    parser.add_argument('--setup-only', action='store_true', help='Install and build without starting the server.')
    parser.add_argument('--no-browser', action='store_true', help='Print the local address without opening a browser.')
    parser.add_argument('--port', type=int, default=8765, help='Local port (default: 8765).')
    parser.add_argument('--data-dir', type=Path, help='Optional directory for the SQLite database; defaults to backend/data.')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535.')
    try:
        npm = prerequisites()
        if args.check:
            return 0
        environment = dict(os.environ)
        # Prevent ambient Python/pip settings from redirecting this isolated installation.
        for name in ('PYTHONPATH', 'PYTHONHOME', 'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER'):
            environment.pop(name, None)
        environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONNOUSERSITE='1')
        if args.data_dir is not None:
            environment['STUDIO_DATA_DIR'] = str(args.data_dir.expanduser().resolve())
        python = install(npm, environment)
        if args.setup_only:
            print('Setup complete. Run this launcher again to open the workbench.', flush=True)
            return 0
        return serve(python, args.port, environment, not args.no_browser)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'\nSetup stopped: {exc}\nSee docs/QUICKSTART.md for troubleshooting. Existing project data has not been deleted.', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nSetup cancelled. Run the launcher again when ready.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    sys.exit(main())
