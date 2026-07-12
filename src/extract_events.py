"""Chronicle LLM event-extraction layer.

Reads the real Enron corpus (SEC filings / emails) from CockroachDB, uses the
local Qwen3-30B (Ollama on johnson) to extract MEANINGFUL dated case events --
partnership formations, resignations, restatements, indictments, key
transactions -- and writes them into chronicle.events + event_actors as an
'llm-extracted' batch, deduped against the documented baseline.

This replaces the seeded baseline with events the agent discovers itself.

Modes:
  --selftest   validate parsing + filtering on a fixed sample; NO model, NO DB write
  --run        real extraction against the live model + database
Args: [--limit N] [--source sec|email]

Deterministic parsing; the only nondeterminism is the LLM. Requires OLLAMA_URL.
"""
import os, sys, json, time, re
import psycopg, requests
from dotenv import load_dotenv
load_dotenv(r"B:\ColdCase\.env")

OLLAMA = os.getenv("OLLAMA_URL", "http://johnson:11434/v1").replace("/v1", "")
MODEL = os.getenv("AGENT_MODEL", "qwen3:30b-a3b-instruct-2507-q4_K_M")
PRINCIPALS = ["Skilling", "Lay", "Fastow", "Causey", "Kopper", "Watkins", "Enron", "LJM", "Chewco"]

PROMPT = """You are building a legal case timeline for the Enron matter.
From the DOCUMENT below, extract only MEANINGFUL dated events: entity formations,
officer appointments/resignations, board actions, transactions, restatements,
investigations, indictments, pleas. IGNORE boilerplate (bios, routine
compensation tables, addresses, generic policy language).

Return STRICT JSON: {"events":[{"date":"YYYY-MM-DD","event":"<=120 chars","actors":["Surname"]}]}
Give the most precise date the text supports: use YYYY-MM-DD, or YYYY-MM, or just YYYY.
Omit an event only if the text gives no year at all.

DOCUMENT:
\"\"\"%s\"\"\"
"""


def _norm_date(d):
    """Accept YYYY-MM-DD, YYYY-MM, or YYYY; normalize to a full date."""
    if not d:
        return None
    d = str(d).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return d
    if re.match(r"^\d{4}-\d{2}$", d):
        return d + "-01"
    if re.match(r"^\d{4}$", d):
        return d + "-01-01"
    return None

def parse_events(raw):
    """Tolerant JSON extraction from a model reply; returns list of clean events."""
    txt = raw.strip()
    if "```" in txt:
        txt = re.sub(r"```(json)?", "", txt).strip()
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except Exception:
        return []
    out = []
    for e in data.get("events", []):
        ev = (e.get("event") or "").strip()
        date = _norm_date(e.get("date"))
        if not ev or not date:
            continue                       # need at least a year
        actors = [a.strip() for a in (e.get("actors") or []) if a and a.strip()]
        if not actors:                     # backfill actors by scanning the text
            actors = [p for p in PRINCIPALS if p.lower() in ev.lower()]
        out.append({"date": date, "event": ev[:120], "actors": actors[:6]})
    return out

def call_model(text, tries=3):
    for i in range(tries):
        try:
            r = requests.post(OLLAMA + "/api/generate", json={"model": MODEL,
                "prompt": PROMPT % text[:3500], "stream": False,
                "options": {"temperature": 0, "num_predict": 512}}, timeout=180)
            return r.json().get("response", "")
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
    return ""


def already_have(cur, ev):
    """Dedup: skip if a very similar event description already exists."""
    key = re.sub(r"[^a-z0-9 ]", "", ev.lower())[:40]
    n = cur.execute("SELECT count(*) FROM chronicle.events "
                    "WHERE regexp_replace(lower(description),'[^a-z0-9 ]','','g') LIKE %s",
                    (f"%{key}%",)).fetchone()[0]
    return n > 0

def run(limit, source):
    conn = psycopg.connect(os.getenv("CRDB_ADMIN_URL"), autocommit=True)
    cur = conn.cursor()
    if source == "email":
        rows = cur.execute("SELECT body FROM emails WHERE length(body) > 400 ORDER BY sent_at LIMIT %s", (limit,)).fetchall()
    else:
        rows = cur.execute("""SELECT text FROM doc_chunks
            WHERE length(text) > 400 AND (text ILIKE '%%LJM%%' OR text ILIKE '%%Raptor%%'
              OR text ILIKE '%%Fastow%%' OR text ILIKE '%%Chewco%%' OR text ILIKE '%%related part%%'
              OR text ILIKE '%%restat%%' OR text ILIKE '%%special purpose%%'
              OR text ILIKE '%%Skilling%%' OR text ILIKE '%%Watkins%%')
            LIMIT %s""", (limit,)).fetchall()
    cur.execute("INSERT INTO chronicle.batches(seq,label) VALUES(99,'llm-extracted') "
                "ON CONFLICT DO NOTHING")
    bid = cur.execute("SELECT batch_id FROM chronicle.batches WHERE label='llm-extracted' LIMIT 1").fetchone()[0]
    added = 0
    for i, (text,) in enumerate(rows):
        events = parse_events(call_model(text))
        for ev in events:
            if already_have(cur, ev["event"]):
                continue
            cur.execute("""INSERT INTO chronicle.events(batch_id,description,event_date,confidence,source,active)
                           VALUES(%s,%s,%s,0.7,%s,true) RETURNING event_id""",
                        (bid, ev["event"], ev["date"], source))
            eid = cur.fetchone()[0]
            for a in ev["actors"]:
                cur.execute("INSERT INTO chronicle.event_actors(event_id,actor,role) VALUES(%s,%s,'mentioned')", (eid, a))
            added += 1
        print(f"  chunk {i+1}/{len(rows)}: +{len(events)} candidate events (running total {added})")
    print(f"DONE: added {added} LLM-extracted events into chronicle.events")
    conn.close()


SAMPLE = '''Sure, here is the JSON:
```json
{"events":[
  {"date":"1999-06-30","event":"LJM Cayman L.P. formed with Fastow as general partner","actors":["Fastow","LJM"]},
  {"date":"2001-08-14","event":"Jeffrey Skilling resigns as CEO of Enron","actors":["Skilling"]},
  {"date":"2001-10-16","event":"Enron announces $1.01B charge and $1.2B equity reduction","actors":["Enron"]},
  {"date":null,"event":"Director compensation policy described","actors":[]},
  {"event":"Boilerplate with no date at all","actors":["Enron"]},
  {"date":"2001-12-02","event":"Enron files for Chapter 11 bankruptcy","actors":[]}
]}
```'''

def selftest():
    evs = parse_events(SAMPLE)
    print("parsed", len(evs), "valid events (boilerplate + undated correctly dropped):")
    for e in evs:
        print("  ", e["date"], "|", e["event"], "| actors:", e["actors"])
    assert len(evs) == 4, "expected 4 dated meaningful events"
    assert all(re.match(r"\d{4}-\d{2}-\d{2}", e["date"]) for e in evs)
    assert evs[-1]["actors"] == ["Enron"], "actor backfill from text failed"
    print("SELFTEST PASS — parsing/filter/actor-backfill logic verified (no model, no DB write)")

def main():
    args = sys.argv[1:]
    limit = int(args[args.index("--limit")+1]) if "--limit" in args else 30
    source = args[args.index("--source")+1] if "--source" in args else "sec"
    if "--run" in args:
        run(limit, source)
    else:
        selftest()

if __name__ == "__main__":
    main()
