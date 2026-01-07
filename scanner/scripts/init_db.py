from __future__ import annotations
from pathlib import Path
from scanner.storage.db import connect, init_db

def main():
    db = Path("data/scanner.sqlite")
    con = connect(db)
    init_db(con)
    print(f"Initialized DB at {db}")

if __name__ == "__main__":
    main()
