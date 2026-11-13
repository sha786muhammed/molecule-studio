"""Check the hosted entry point through HTTP, including real xTB and isolation."""
import argparse
import json
import time
import urllib.error
import urllib.request
from http.cookies import SimpleCookie


class Browser:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.cookie = ''

    def request(self, path, body=None):
        headers = {'Cookie': self.cookie}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers)
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.headers.get('Set-Cookie'):
                cookies = SimpleCookie(response.headers['Set-Cookie'])
                self.cookie = 'studio_session=' + cookies['studio_session'].value
            content = response.read().decode()
            return json.loads(content) if 'application/json' in response.headers.get('Content-Type', '') else content


def check(base_url):
    alice, bob = Browser(base_url), Browser(base_url)
    deadline = time.monotonic() + 180
    while True:
        try:
            health = alice.request('/api/health')
            break
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(.5)
    assert health['demo'] and health['status'] == 'ready', health
    assert '<div id="root">' in alice.request('/'), 'Built React document was not served.'
    water = next(m for m in alice.request('/api/molecules') if m['name'] == 'Water')
    j = alice.request('/api/jobs', {'molecule_id': water['id'], 'method': 'GFN2-xTB', 'task': 'singlepoint'})
    path = '/api/jobs/' + j['id']
    deadline = time.monotonic() + 120
    while j['status'] in ('queued', 'running'):
        if time.monotonic() > deadline:
            raise RuntimeError('Water calculation did not finish within 120 seconds.')
        time.sleep(.2)
        j = alice.request(path)
    assert j['status'] == 'completed', j.get('error', j['status'])
    assert j['result']['energy'] < 0 and j['result']['energy_unit'] == 'Hartree'
    assert alice.request(path + '/export/xyz').splitlines()[0] == '3'
    assert bob.request('/api/jobs') == [], 'A second visitor received the first visitor’s jobs.'
    for route in (path, path + '/export/json', '/requirements.txt'):
        try:
            bob.request(route)
        except urllib.error.HTTPError as error:
            assert error.code == 404, error.code
        else:
            raise AssertionError('Unexpected access to ' + route)
    print('Hosted frontend, real water xTB, XYZ export and visitor isolation passed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:10000')
    check(parser.parse_args().base_url)
