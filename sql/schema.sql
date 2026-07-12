-- Chronicle: the living theory of the case.
-- Lives in a `chronicle` schema inside the shared coldcase DB so it can read
-- the already-embedded corpus (emails + SEC filings) directly.
-- Apply: psql "$CRDB_ADMIN_URL" -f sql/schema.sql

USE coldcase;
CREATE SCHEMA IF NOT EXISTS chronicle;

-- A batch = a wave of discovery documents (rolling review).
CREATE TABLE IF NOT EXISTS chronicle.batches (
  batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  seq INT, label STRING, ingested_at TIMESTAMPTZ DEFAULT now()
);

-- Extracted events. active/superseded model the *revisable* nature.
CREATE TABLE IF NOT EXISTS chronicle.events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id UUID REFERENCES chronicle.batches,
  description STRING NOT NULL,
  event_date DATE,
  confidence FLOAT8 DEFAULT 0.5,
  source STRING,
  excerpt STRING,
  active BOOL DEFAULT true,
  extracted_at TIMESTAMPTZ DEFAULT now(),
  INDEX (event_date), INDEX (active)
);

CREATE TABLE IF NOT EXISTS chronicle.event_actors (
  event_id UUID REFERENCES chronicle.events,
  actor STRING NOT NULL,
  role STRING,
  PRIMARY KEY (event_id, actor)
);

-- Contradictions between events (same actors, conflicting dates, etc.).
CREATE TABLE IF NOT EXISTS chronicle.conflicts (
  conflict_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_a UUID REFERENCES chronicle.events,
  event_b UUID REFERENCES chronicle.events,
  kind STRING,
  detected_at TIMESTAMPTZ DEFAULT now(),
  status STRING DEFAULT 'open'
);

-- The PERSISTED resolution - the core of "memory is central".
CREATE TABLE IF NOT EXISTS chronicle.resolutions (
  resolution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conflict_id UUID REFERENCES chronicle.conflicts,
  chosen_event UUID REFERENCES chronicle.events,
  rationale STRING,
  resolved_by STRING,
  resolved_at TIMESTAMPTZ DEFAULT now()
);

-- The evolving legal theory: claims whose confidence changes as evidence lands.
CREATE TABLE IF NOT EXISTS chronicle.theory_claims (
  claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  statement STRING NOT NULL,
  confidence FLOAT8 DEFAULT 0.5,
  status STRING DEFAULT 'open',
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chronicle.theory_evidence (
  claim_id UUID REFERENCES chronicle.theory_claims,
  event_id UUID REFERENCES chronicle.events,
  stance STRING,
  PRIMARY KEY (claim_id, event_id)
);

-- Confidence over time = the convergence curve (the ablation money shot).
CREATE TABLE IF NOT EXISTS chronicle.theory_history (
  claim_id UUID REFERENCES chronicle.theory_claims,
  batch_seq INT,
  confidence FLOAT8,
  ts TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (claim_id, batch_seq)
);

-- Sealed ground truth (documented Enron chronology) - agent can't read it.
CREATE SCHEMA IF NOT EXISTS chronicle_truth;
CREATE TABLE IF NOT EXISTS chronicle_truth.events (
  gt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  description STRING, event_date DATE, actors STRING[]
);
