"""Seed the documented Enron chronology as sealed ground truth (public record).
The agent's role has no access to chronicle_truth - convergence is scored blind.
"""
import os
import psycopg
from dotenv import load_dotenv

load_dotenv(r"B:\ColdCase\.env")

# Public, well-documented Enron events (Powers Report / trial record / press).
GT = [
    ("LJM2 partnership formed by CFO Andrew Fastow", "1999-10-01", ["Fastow"]),
    ("Enron stock peaks near $90", "2000-08-23", []),
    ("Jeffrey Skilling becomes CEO", "2001-02-12", ["Skilling"]),
    ("Skilling resigns as CEO", "2001-08-14", ["Skilling"]),
    ("Sherron Watkins warns Lay of accounting scandal", "2001-08-15",
     ["Watkins", "Lay"]),
    ("Q3 2001 results disclose $618M loss", "2001-10-16", []),
    ("SEC opens inquiry into Enron", "2001-10-22", []),
    ("Andrew Fastow ousted as CFO", "2001-10-24", ["Fastow"]),
    ("Enron restates earnings 1997-2001", "2001-11-08", []),
    ("Dynegy merger collapses", "2001-11-28", []),
    ("Enron files for Chapter 11 bankruptcy", "2001-12-02", []),
    ("DOJ forms Enron criminal task force", "2002-01-09", []),
    ("Michael Kopper pleads guilty", "2002-08-21", ["Kopper"]),
    ("Andrew Fastow indicted", "2002-10-31", ["Fastow"]),
    ("Andrew Fastow pleads guilty", "2004-01-14", ["Fastow"]),
    ("Lay and Skilling indicted", "2004-07-08", ["Lay", "Skilling"]),
    ("Lay and Skilling convicted of fraud", "2006-05-25", ["Lay", "Skilling"]),
]


def main():
    c = psycopg.connect(os.environ["CRDB_ADMIN_URL"], autocommit=True)
    c.execute("DELETE FROM chronicle_truth.events WHERE true")
    for desc, date, actors in GT:
        c.execute("INSERT INTO chronicle_truth.events (description, event_date,"
                  " actors) VALUES (%s,%s,%s)", (desc, date, actors))
    n = c.execute("SELECT count(*) FROM chronicle_truth.events").fetchone()[0]
    print(f"seeded {n} ground-truth Enron events")


if __name__ == "__main__":
    main()
