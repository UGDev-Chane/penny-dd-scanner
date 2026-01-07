from __future__ import annotations
from typing import Any, Iterable

def cik_pad(cik: str) -> str:
    c = "".join(ch for ch in str(cik) if ch.isdigit())
    return c.zfill(10)

def recent_filings(submissions_json: dict) -> list[dict]:
    # Normalize recent filings list from submissions JSON.
    rec = submissions_json.get("filings", {}).get("recent", {})
    forms = rec.get("form", []) or []
    acc = rec.get("accessionNumber", []) or []
    filed = rec.get("filingDate", []) or []
    primary = rec.get("primaryDocument", []) or []
    out = []
    n = min(len(forms), len(acc), len(filed))
    for i in range(n):
        out.append({
            "form": forms[i],
            "accession": acc[i],
            "filed_at": filed[i],
            "primary_doc": primary[i] if i < len(primary) else None,
        })
    return out
