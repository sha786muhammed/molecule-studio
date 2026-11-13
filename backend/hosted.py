"""Temporary, isolated browser workspaces for a resource-limited public demo."""
import hashlib
import hmac
import os
import re
import secrets
import time
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlsplit
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from backend import storage
from backend.app import initialize_workspace
from backend.web import create_local_app

TTL = 86400
COOKIE = 'studio_session'


class BrowserWorkspaces:
    def __init__(self, app, secret):
        self.app = app
        self.secret = secret

    def session(self, headers):
        cookies = SimpleCookie()
        try:
            cookies.load(headers.get('cookie', ''))
            token = cookies[COOKIE].value if COOKIE in cookies else ''
            payload, signature = token.rsplit('.', 1)
            timestamp, nonce = payload.split('.', 1)
            age = time.time() - int(timestamp)
            expected = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
            if 0 <= age < TTL and re.fullmatch('[0-9a-f]{64}', nonce) and hmac.compare_digest(expected, signature):
                return hashlib.sha256(payload.encode()).hexdigest(), None
        except (ValueError, KeyError, OverflowError, CookieError):
            pass
        payload = f'{int(time.time())}.{secrets.token_hex(32)}'
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        return hashlib.sha256(payload.encode()).hexdigest(), payload + '.' + signature

    def initialize(self):
        with storage.LOCK:
            if storage.database().exists():
                return
            directory = storage.database().parent
            directory.mkdir(parents=True, exist_ok=True)
            for path in directory.glob('*.sqlite3'):
                if time.time() - path.stat().st_mtime > TTL:
                    path.unlink()
            if len(list(directory.glob('*.sqlite3'))) >= 64:
                return False
            initialize_workspace()
        return True

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope['headers']}
        if scope['method'] not in ('GET', 'HEAD', 'OPTIONS') and headers.get('origin'):
            if urlsplit(headers['origin']).netloc != headers.get('host'):
                return await JSONResponse({'detail': 'Open this app directly to make changes.'}, status_code=403)(scope, receive, send)
        workspace, token = self.session(headers)
        context_token = storage.WORKSPACE.set(workspace)
        try:
            # A plain health check must not allocate disk or seed molecules.
            if scope['path'].startswith('/api/') and scope['path'] != '/api/health':
                if await run_in_threadpool(self.initialize) is False:
                    return await JSONResponse({'detail': 'The free demo is at capacity. Please try again later.'}, status_code=503)(scope, receive, send)

            async def with_cookie(message):
                if message['type'] == 'http.response.start':
                    message.setdefault('headers', []).append((b'cache-control', b'no-store'))
                    if token:
                        cookie = f'{COOKIE}={token}; Path=/; Max-Age={TTL}; HttpOnly; Secure; SameSite=Strict'
                        message['headers'].append((b'set-cookie', cookie.encode()))
                await send(message)
            await self.app(scope, receive, with_cookie)
        finally:
            storage.WORKSPACE.reset(context_token)


def create_hosted_app(frontend_dir=None):
    if os.environ.get('STUDIO_DEMO') != '1':
        raise RuntimeError('Hosted serving requires STUDIO_DEMO=1. Use backend.web for a local workspace.')
    application = create_local_app(frontend_dir)
    application.title = 'Molecule Studio — free demo'
    secret = os.environ.get('STUDIO_SESSION_SECRET', '').encode() or secrets.token_bytes(32)
    application.add_middleware(BrowserWorkspaces, secret=secret)
    return application
