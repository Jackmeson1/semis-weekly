"""HTTP fetches: every response body is archived and logged as a row in raw_fetch.

The contact email goes into the User-Agent only for SEC requests; every other source gets a generic one.
"""
import datetime as dt
import gzip
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from .config import ROOT, env

# Identify the client honestly. FRED drops requests whose User-Agent does not match the TLS
# fingerprint: python-requests without the python-requests token times out (tested 2026-10-28).
GENERIC_UA = f'{requests.utils.default_user_agent()} semis-weekly/0.1'
SEC_MIN_INTERVAL = 0.15  # SEC allows at most 10 requests per second
_last_sec_call = 0.0


def _is_sec(url):
    host = urlparse(url).hostname or ''
    return host == 'sec.gov' or host.endswith('.sec.gov')


def user_agent(url):
    if not _is_sec(url):
        return GENERIC_UA
    e = env()
    if not e.get('CONTACT_EMAIL'):
        raise RuntimeError('SEC requests need CONTACT_EMAIL in .env')
    return f"{e.get('CONTACT_NAME') or 'semis-weekly'} {e['CONTACT_EMAIL']}"


def get(con, source, series_id, url, entity='', ext='dat', compress=False):
    """Return (fetch_id, retrieved_at, body or None, error or None). compress=True gzips the archived file."""
    global _last_sec_call
    if _is_sec(url):
        wait = SEC_MIN_INTERVAL - (time.monotonic() - _last_sec_call)
        if wait > 0:
            time.sleep(wait)
        _last_sec_call = time.monotonic()

    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    fetch_id = f'{series_id}:{entity}:{now:%Y%m%dT%H%M%S%f}'
    status, body, error = None, b'', None
    try:
        r = requests.get(url, headers={'User-Agent': user_agent(url)}, timeout=30)
        status, body = r.status_code, r.content
        if r.status_code != 200:
            error = f'HTTP {r.status_code}'
    except requests.RequestException as e:
        error = f'{type(e).__name__}: {e}'

    name = re.sub(r'[^A-Za-z0-9._-]+', '_', fetch_id) + '.' + ext + ('.gz' if compress else '')
    rel = Path('data') / 'raw' / f'{now:%Y}' / f'{now:%m}' / f'{now:%d}' / name
    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / rel).write_bytes(gzip.compress(body) if compress else body)
    con.execute('INSERT INTO raw_fetch VALUES (?,?,?,?,?,?,?,?,?,?)',
                [fetch_id, source, series_id, entity, url, now, status,
                 hashlib.sha256(body).hexdigest(), rel.as_posix(), error])
    return fetch_id, now, (None if error else body), error
