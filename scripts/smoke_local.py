#!/usr/bin/env python3
"""Exercise the real local launcher and examples with an isolated temporary database."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def run(output, port):
    with tempfile.TemporaryDirectory(prefix='molecule-studio-smoke-') as directory:
        temporary = Path(directory)
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        url = f'http://127.0.0.1:{port}'
        log_path = temporary / 'launcher.log'
        with log_path.open('w') as log:
            options = {'start_new_session':True} if os.name != 'nt' else {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP}
            process = subprocess.Popen([sys.executable, str(ROOT / 'launch.py'), '--no-browser',
                                        '--port', str(port), '--data-dir', str(temporary / 'data')],
                                       cwd=temporary, env=environment, stdout=log, stderr=subprocess.STDOUT, **options)
            try:
                deadline = time.monotonic() + 300
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError('Launcher exited before the app became ready.')
                    try:
                        with urllib.request.urlopen(url + '/api/health', timeout=1) as response:
                            if json.load(response).get('status') == 'ready':
                                break
                    except (urllib.error.URLError, TimeoutError, ValueError):
                        pass
                    time.sleep(0.2)
                else:
                    raise RuntimeError('Launcher did not become ready within 300 seconds.')
                with urllib.request.urlopen(url) as response:
                    if '<div id="root">' not in response.read().decode():
                        raise RuntimeError('The built frontend was not served.')
                for path in ('/api/not-a-route', '/requirements.txt'):
                    try:
                        urllib.request.urlopen(url + path)
                    except urllib.error.HTTPError as exc:
                        if exc.code != 404:
                            raise
                    else:
                        raise RuntimeError('Unexpected frontend/file response for ' + path)
                subprocess.run([sys.executable, str(ROOT / 'examples' / 'run_examples.py'),
                                '--base-url', url, '--output', str(output)], cwd=temporary, env=environment, check=True)
                if not (temporary / 'data' / 'studio.sqlite3').is_file():
                    raise RuntimeError('The configured separate data directory was not used.')
                print('Frontend, API, isolated data directory and scientific examples passed.', flush=True)
            except Exception:
                print(log_path.read_text(), file=sys.stderr)
                raise
            finally:
                if process.poll() is None:
                    if os.name == 'nt':
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        if os.name == 'nt':
                            process.kill()
                        else:
                            os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
        if process.returncode not in (0, 130):
            raise RuntimeError(f'Launcher shutdown returned {process.returncode}.\n' + log_path.read_text())
        try:
            urllib.request.urlopen(url + '/api/health', timeout=1)
        except (urllib.error.URLError, TimeoutError):
            print('Launcher and calculation server stopped cleanly.', flush=True)
        else:
            raise RuntimeError('A calculation server remained running after shutdown.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'examples' / 'results')
    parser.add_argument('--port', type=int, default=8765)
    arguments = parser.parse_args()
    run(arguments.output.resolve(), arguments.port)
