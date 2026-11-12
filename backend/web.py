"""Serve the built local interface and scientific API from one loopback port."""
import argparse
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app import app as scientific_api


def create_local_app(frontend_dir=None):
    frontend = Path(frontend_dir) if frontend_dir is not None else Path(__file__).resolve().parents[1] / 'dist' / 'client'
    if not (frontend / 'index.html').is_file():
        raise RuntimeError('Frontend build is missing. Run python3 launch.py to install and build the app.')
    application = FastAPI(title='Molecule Studio — local research edition', version='0.1.0')
    application.include_router(scientific_api.router)
    application.mount('/', StaticFiles(directory=frontend, html=True), name='frontend')
    return application


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535.')
    import uvicorn
    uvicorn.run(create_local_app(), host='127.0.0.1', port=args.port, workers=1)


if __name__ == '__main__':
    main()
