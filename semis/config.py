"""Project paths, .env, the YAML configs, and the report language."""
import datetime as dt
import functools
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
# A language is a folder: playbook/<lang>/ in the repo, or private/playbook/<lang>/ for one kept out of it
LANG_DIRS = (ROOT / 'playbook', ROOT / 'private' / 'playbook')


def env():
    vals = {}
    p = ROOT / '.env'
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            vals[k.strip()] = v.strip()
    vals.update({k: v for k, v in os.environ.items() if k.startswith(('CONTACT_', 'SEMIS_'))})
    return vals


def lang():
    """Report language: --lang on the command line, else SEMIS_LANG in .env, else en."""
    return env().get('SEMIS_LANG') or 'en'


def playbook_dir(language=None):
    """Everything language-specific: the rulebook, style guide, glossary, prompt template and locale.yaml."""
    language = language or lang()
    for base in LANG_DIRS:
        if (base / language).is_dir():
            return base / language
    raise SystemExit(f'No playbook for language "{language}": expected playbook/{language}/ '
                     f'or private/playbook/{language}/')


@functools.lru_cache(maxsize=None)
def _yaml_in(language, name):
    p = playbook_dir(language) / name
    return yaml.safe_load(p.read_text(encoding='utf-8')) if p.exists() else {}


def locale(language=None):
    """Page text (ui), level-1 prompt pieces (prompt), and names that replace the English ones (names)."""
    return _yaml_in(language or lang(), 'locale.yaml')


def glossary(language=None):
    """Reader-facing name for each internal ID."""
    return _yaml_in(language or lang(), 'glossary.yaml')


def registry():
    return yaml.safe_load((ROOT / 'sources' / 'registry.yaml').read_text(encoding='utf-8'))


def signal_defs():
    defs = yaml.safe_load((ROOT / 'signals' / 'signals.yaml').read_text(encoding='utf-8'))
    for c, meta in defs['channels'].items():
        meta['id'] = c
    return defs


# Internal IDs of signals and rules (S-L3-03, S-L3-01/02, HZ-03, NOVETO-01, CH-B, SW-m-02 ...).
# They belong in json blocks and tooltips; prose uses the names in the language's glossary.yaml.
ID_RE = re.compile(r'(?<![A-Za-z0-9-])(?:S-L\d-\d{2}(?:/\d{2})*|(?:NO)?VETO-\d{2}|HZ-\d{2}|INF-\d{2}|CAL-\d{2}'
                   r'|ACT-\d{2}|INV-\d{2}|SW-[a-z]-\d{2}|CH-[A-D])(?![A-Za-z0-9])')


def expand_id(token):
    """S-L3-01/02 -> [S-L3-01, S-L3-02]; anything else -> [token]."""
    head, *tails = token.split('/')
    return [head] + [head[:-2] + t for t in tails]


def localized(item, key, language=None):
    """A channel's or signal's name or note: the language's override from locale.yaml, else the English in signals.yaml."""
    override = locale(language).get('names', {}).get(item.get('id'), {})
    return override.get(key) or item.get(key)


def run_id(day):
    y, w, _ = day.isocalendar()
    return f'{y}-W{w:02d}'


def parse_date(s):
    return dt.date.fromisoformat(str(s)[:10])
