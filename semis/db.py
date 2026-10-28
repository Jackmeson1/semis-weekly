"""DuckDB connection and point-in-time reads."""
import duckdb

from .config import ROOT

DB_PATH = ROOT / 'data' / 'semis.duckdb'


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute((ROOT / 'schema' / 'schema.sql').read_text(encoding='utf-8'))
    return con


def series(con, series_id, entity='', asof=None, cutoff=None):
    """Return [(obs_date, value)] in ascending date order.

    asof: only observations with obs_date <= asof that had been released by asof
          (rows without released_at are not filtered). Backfilled signals rely on this
          so they never see a quarterly or monthly report that was published later.
    cutoff: only versions first seen at or before cutoff (for backtests); default is the latest version.
    """
    sql = """
        SELECT obs_date, value FROM (
          SELECT obs_date, value, released_at,
                 row_number() OVER (PARTITION BY obs_date ORDER BY first_seen_at DESC) AS rn
          FROM observations
          WHERE series_id = ? AND entity = ? AND (? IS NULL OR first_seen_at <= ?)
        ) WHERE rn = 1 AND value IS NOT NULL AND (? IS NULL OR obs_date <= ?)
          AND (? IS NULL OR released_at IS NULL OR CAST(released_at AS DATE) <= ?)
        ORDER BY obs_date"""
    return con.execute(sql, [series_id, entity, cutoff, cutoff, asof, asof, asof, asof]).fetchall()
