-- semis-weekly DuckDB schema
-- Flow: archive raw responses -> point-in-time observations -> code computes signals -> models judge -> calibrate later

-- 1. Raw fetches: every response body is kept so results can be checked and recomputed
CREATE TABLE IF NOT EXISTS raw_fetch (
  fetch_id      VARCHAR PRIMARY KEY,          -- {series_id}:{entity}:{retrieved_at ISO}
  source        VARCHAR NOT NULL,             -- source name from registry.yaml
  series_id     VARCHAR NOT NULL,
  entity        VARCHAR NOT NULL DEFAULT '',
  url           VARCHAR NOT NULL,
  retrieved_at  TIMESTAMP NOT NULL,
  http_status   INTEGER,
  sha256        VARCHAR NOT NULL,
  path          VARCHAR NOT NULL,             -- data/raw/YYYY/MM/DD/<fetch_id>.<ext>
  error         VARCHAR                       -- failure reason; null on success
);

-- 2. Observations, point-in-time: a revision to (series, entity, obs_date) adds a row, never overwrites
CREATE TABLE IF NOT EXISTS observations (
  series_id     VARCHAR NOT NULL,
  entity        VARCHAR NOT NULL DEFAULT '',  -- MSFT, SPY, 2330; empty string for macro series
  obs_date      DATE NOT NULL,                -- the date or period end the value belongs to
  value         DOUBLE,
  unit          VARCHAR NOT NULL,
  layer         VARCHAR NOT NULL,             -- e.g. L1.long_end
  first_seen_at TIMESTAMP NOT NULL,           -- when we first saw this value
  released_at   TIMESTAMP,                    -- official release time, when available
  fetch_id      VARCHAR NOT NULL,
  PRIMARY KEY (series_id, entity, obs_date, first_seen_at)
);

-- latest version of every observation
CREATE OR REPLACE VIEW obs_latest AS
SELECT * EXCLUDE (rn) FROM (
  SELECT *, row_number() OVER (PARTITION BY series_id, entity, obs_date ORDER BY first_seen_at DESC) AS rn
  FROM observations
) WHERE rn = 1;
-- For backtests: WHERE first_seen_at <= <point in time>, then take the latest per key, so nothing unpublished leaks in

-- 3. Events: auctions, FOMC meetings, earnings releases and other discrete events
CREATE TABLE IF NOT EXISTS events (
  event_id   VARCHAR PRIMARY KEY,             -- auction:2026-10-27:5-Year
  kind       VARCHAR NOT NULL,                -- auction / fomc / earnings / data_release
  layer      VARCHAR NOT NULL,
  event_date DATE NOT NULL,
  entity     VARCHAR NOT NULL DEFAULT '',
  payload    JSON,                            -- auctions: highYield, bidToCoverRatio, ...
  fetch_id   VARCHAR
);

-- 4. Signals: computed by code from signals/signals.yaml, one row per signal per issue
CREATE TABLE IF NOT EXISTS signals (
  run_id     VARCHAR NOT NULL,                -- 2026-W44
  signal_id  VARCHAR NOT NULL,                -- S-L1-01
  layer      VARCHAR NOT NULL,
  as_of      DATE NOT NULL,                   -- latest data date used in this issue
  value      DOUBLE,
  state      VARCHAR NOT NULL,                -- slack / watch / binding / na (no data)
  detail     JSON,                            -- inputs, window, thresholds, prior value
  PRIMARY KEY (run_id, signal_id)
);

-- 4b. Signal history: each weekly run writes a row (mode = live); past weeks can be backfilled (mode = backfill)
--     Backfill uses the current data vintage filtered by released_at; revised values cannot be restored
CREATE TABLE IF NOT EXISTS signal_history (
  run_id      VARCHAR NOT NULL,
  signal_id   VARCHAR NOT NULL,
  layer       VARCHAR NOT NULL,
  as_of       DATE NOT NULL,
  value       DOUBLE,
  state       VARCHAR NOT NULL,
  detail      JSON,
  computed_at TIMESTAMP NOT NULL,
  mode        VARCHAR NOT NULL,                -- live / backfill
  PRIMARY KEY (run_id, signal_id)
);

-- 5. Judgments, aggregated in three levels. Each level cites only the level below
--    level 1 = channel (scope C1–C7), level 2 = horizon (near / mid / far), level 3 = synthesis (scope all)
CREATE TABLE IF NOT EXISTS judgments (
  run_id      VARCHAR NOT NULL,
  level       SMALLINT NOT NULL,              -- 1 / 2 / 3
  scope       VARCHAR NOT NULL,               -- C1 / mid / all
  item        VARCHAR NOT NULL,               -- state / horizon:mid / chain:CH-A / invariant:INV-01 / action
  verdict     VARCHAR NOT NULL,
  signal_refs VARCHAR[],                      -- only level 1 cites signals directly
  rule_refs   VARCHAR[],                      -- ['VETO-01', 'SW-M-07']
  input_refs  VARCHAR[],                      -- judgments one level down, e.g. ['1:C1:state', '1:C2:horizon:mid']
  deviation   VARCHAR,                        -- which rule was departed from and why; null if none
  confidence  VARCHAR,                        -- high / medium / low
  PRIMARY KEY (run_id, level, scope, item)
);

-- 6. Log files: one Markdown file per level and scope; the page is built from these
CREATE TABLE IF NOT EXISTS logs (
  run_id     VARCHAR NOT NULL,
  level      SMALLINT NOT NULL,
  scope      VARCHAR NOT NULL,
  path       VARCHAR NOT NULL,                -- logs/2026-W44/C1-credit.md
  sha256     VARCHAR NOT NULL,
  created_at TIMESTAMP NOT NULL,
  model      VARCHAR,                         -- model that wrote the log
  PRIMARY KEY (run_id, level, scope)
);

-- 7. Calibration: 4–8 weeks later, record whether a judgment held and whether a threshold should move
CREATE TABLE IF NOT EXISTS calibration (
  run_id           VARCHAR NOT NULL,
  item             VARCHAR NOT NULL,          -- level:scope:item of the judgment
  reviewed_at      DATE NOT NULL,
  outcome          VARCHAR NOT NULL,          -- right / wrong / unclear
  note             VARCHAR,
  threshold_change VARCHAR,                   -- e.g. S-L1-01 binding 20bp -> 15bp
  PRIMARY KEY (run_id, item, reviewed_at)
);
