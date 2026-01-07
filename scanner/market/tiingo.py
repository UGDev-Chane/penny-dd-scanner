from __future__ import annotations
import os
import requests
import pandas as pd
from datetime import date
from typing import Optional

TIINGO_BASE = "https://api.tiingo.com/tiingo"

class TiingoClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TIINGO_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing TIINGO_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Token {self.api_key}"})

    def eod_prices(self, symbols: list[str], start: date, end: date) -> pd.DataFrame:
        # Tiingo supports per-symbol endpoints. For MVP, loop.
        rows = []
        for sym in symbols:
            url = f"{TIINGO_BASE}/daily/{sym}/prices"
            params = {
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
                "format": "json",
                "resampleFreq": "daily",
            }
            r = self.session.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            for d in data:
                rows.append({
                    "symbol": sym,
                    "date": d["date"][:10],
                    "open": d.get("open"),
                    "high": d.get("high"),
                    "low": d.get("low"),
                    "close": d.get("close"),
                    "volume": d.get("volume"),
                })
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["dollar_volume"] = df["close"] * df["volume"]
        return df
