#!/usr/bin/env python3
"""Run three real calculations against an already-running local workbench."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import sys
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent


def request(base, path, payload=None, raw=False):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + '/api' + path, data=data,
                                 headers={'Content-Type':'application/json'} if data is not None else {})
    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read()
    return content if raw else json.loads(content)


def validate(case, result):
    if not result.get('converged') or not math.isfinite(result['energy']):
        raise ValueError(case['id'] + ': no finite, converged result.')
    expected_unit = 'Hartree' if case['method'] == 'GFN2-xTB' else 'kcal/mol'
    if result['energy_unit'] != expected_unit:
        raise ValueError(case['id'] + ': unexpected energy unit.')
    if case['id'] == 'water-xtb':
        if len(result.get('charges') or []) != 3 or abs(sum(result['charges'])) > 1e-5:
            raise ValueError('Water charges do not sum to the neutral molecular charge.')
        if not 0.5 < result['dipole'] < 4:
            raise ValueError('Water dipole is outside this broad sanity interval.')
        frequencies = result.get('frequencies') or []
        if len(frequencies) != 3 or any(f['wavenumber'] < 1000 for f in frequencies):
            raise ValueError('Water must have three positive internal modes above 1000 cm^-1 in this example.')
    if case['id'] == 'ethanol-mmff' and result['energy'] > result['initial_energy'] + 1e-7:
        raise ValueError('Ethanol optimization increased the force-field energy.')
    if case['task'] == 'conformers':
        conformers = result['conformers']
        if len(conformers) < 2 or abs(conformers[0]['relative_energy']) > 1e-8:
            raise ValueError('Butane must have at least two distinct sampled conformers, referenced to zero.')
        energies = [c['energy'] for c in conformers]
        if energies != sorted(energies) or not all(c['converged'] for c in conformers):
            raise ValueError('The conformer ranking contains unordered or unconverged energies.')


def run(base, output):
    health = request(base, '/health')
    project = request(base, '/projects', {'name':'Getting started examples',
                                        'description':'Water, ethanol and butane validation examples.'})
    output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for case in json.loads((HERE / 'cases.json').read_text()):
        print('Running ' + case['id'] + '…', flush=True)
        molecule = request(base, '/molecules', {'name':case['name'], 'content':case['smiles'],
                                               'kind':'smiles', 'project_id':project['id']})
        settings = {k:v for k,v in case.items() if k not in ('id','name','smiles')}
        job = request(base, '/jobs', {'molecule_id':molecule['id'], 'charge':0,
                                     'multiplicity':1, 'solvent':'gas', **settings})
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            job = request(base, '/jobs/' + job['id'])
            if job['status'] not in ('running','queued'):
                break
            time.sleep(0.2)
        if job['status'] != 'completed':
            raise ValueError(f'{case["id"]}: {job["status"]}: {job.get("error", "calculation did not finish within 180 seconds")}')
        result = job['result']
        validate(case, result)
        (output / (case['id'] + '.json')).write_text(json.dumps(job, indent=2))
        for extension in ('xyz', 'sdf'):
            content = request(base, f'/jobs/{job["id"]}/export/{extension}', raw=True)
            (output / (case['id'] + '.' + extension)).write_bytes(content)
        summaries.append({'case':case['id'], 'method':result['method'],
                          'energy':result['energy'], 'energy_unit':result['energy_unit'],
                          'converged':result['converged'], 'dipole_debye':result.get('dipole'),
                          'internal_frequencies_cm-1':[f['wavenumber'] for f in result.get('frequencies') or []],
                          'conformer_relative_energies_kcal_mol':[c['relative_energy'] for c in result.get('conformers',[])],
                          'engine':result['engine'], 'checks':'passed'})
        print(f'  passed: {result["energy"]:.8f} {result["energy_unit"]}', flush=True)
    summary = {'recorded_utc':datetime.now(timezone.utc).isoformat(), 'platform':platform.platform(),
               'engines':health['engines'], 'examples':summaries,
               'interpretation':'Method-specific computational examples; not experimental validation or a guarantee for other molecules.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    print('All three examples passed. Results: ' + str(output.resolve()), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--output', type=Path, default=HERE / 'results')
    args = parser.parse_args()
    try:
        run(args.base_url.rstrip('/'), args.output)
    except (OSError, urllib.error.URLError, ValueError, KeyError) as exc:
        print('Example run failed: ' + str(exc) + '\nStart the app with python3 launch.py first.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
