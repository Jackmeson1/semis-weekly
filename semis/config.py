"""Project paths, .env, the two YAML configs, and the report language."""
import datetime as dt
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LANGS = ('zh', 'en')


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
    """Report language: --lang on the command line, else SEMIS_LANG in .env, else zh."""
    value = env().get('SEMIS_LANG', 'zh')
    return value if value in LANGS else 'zh'


def playbook_dir(language=None):
    return ROOT / 'playbook' / (language or lang())


def registry():
    return yaml.safe_load((ROOT / 'sources' / 'registry.yaml').read_text(encoding='utf-8'))


def signal_defs():
    return yaml.safe_load((ROOT / 'signals' / 'signals.yaml').read_text(encoding='utf-8'))


def localized(item, key, language=None):
    """Pick item['<key>_en'] for English when present, else item[key]."""
    if (language or lang()) == 'en' and item.get(f'{key}_en'):
        return item[f'{key}_en']
    return item.get(key)


def run_id(day):
    y, w, _ = day.isocalendar()
    return f'{y}-W{w:02d}'


def parse_date(s):
    return dt.date.fromisoformat(str(s)[:10])
