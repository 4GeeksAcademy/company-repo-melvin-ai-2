"""Load valid analyzer rows into the incident manager.

    uv run python scripts/seed_incidents.py

Each row is stored with origin customer. Invalid rows are printed and skipped.
Running the script again does not insert the same CSV id twice.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "services" / "api"
for path in (ROOT, API):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from sqlmodel import Session  # noqa: E402

from app.incidents.service import seed_csv  # noqa: E402
from app.inventory.db import get_engine, init_inventory_db  # noqa: E402

DEFAULT_CSV = ROOT / "scripts" / "incidents-brasaland.csv"


def main() -> None:
    init_inventory_db()
    with Session(get_engine()) as session:
        inserted, already, _notes = seed_csv(session, DEFAULT_CSV)
    print(f"Inserted {inserted} incidents. Already loaded {already}.")


if __name__ == "__main__":
    main()
