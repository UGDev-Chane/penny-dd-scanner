from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .tiingo import TiingoClient


@dataclass
class MarketSnapshot:
    price: Optional[float] = None
    market_cap: Optional[float] = None
    avg_daily_volume: Optional[float] = None  # shares


def get_market_snapshot(ticker: str) -> MarketSnapshot:
    """
    v1: Market snapshot from Tiingo daily prices.

    - price: most recent close in the window
    - avg_daily_volume: mean daily volume over last 20 trading days (approx)
    - market_cap: TiingoClient doesn't expose metadata in your current file.
      We attempt Tiingo /daily/{ticker} metadata call via the same session.
      If absent, returns None.
    """
    sym = ticker.upper().strip()
    c = TiingoClient()

    # Pull ~45 calendar days to cover ~20 trading days reliably
    end = date.today()
    start = end - timedelta(days=45)

    df = c.eod_prices([sym], start=start, end=end)
    if df is None or df.empty:
        return MarketSnapshot()

    # Ensure sorted
    df = df.sort_values(["date"])
    last_close = df.iloc[-1]["close"]
    # Use last 20 rows (approx last 20 sessions)
    tail = df.tail(20)
    avg_vol = float(tail["volume"].mean()) if "volume" in tail.columns else None

    market_cap = None
    # Best-effort metadata fetch: /tiingo/daily/{sym}
    try:
        url = f"https://api.tiingo.com/tiingo/daily/{sym}"
        r = c.session.get(url, timeout=30)
        r.raise_for_status()
        meta = r.json()
        # Tiingo may include marketCap depending on plan and ticker
        market_cap = meta.get("marketCap") or meta.get("marketcap")
    except Exception:
        market_cap = None

    return MarketSnapshot(
        price=float(last_close) if last_close is not None else None,
        market_cap=float(market_cap) if market_cap is not None else None,
        avg_daily_volume=float(avg_vol) if avg_vol is not None else None,
    )
