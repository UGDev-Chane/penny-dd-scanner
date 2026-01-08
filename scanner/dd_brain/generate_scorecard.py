from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from scanner.utils.env import load_env
load_env()

DD_DIR = Path(__file__).parent
REPORTS_DIR = DD_DIR / "reports"


def load_md(name: str) -> str:
    p = DD_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"Missing markdown template: {p}")
    return p.read_text(encoding="utf-8")


@dataclass
class BasicMarketSnapshot:
    price: Optional[float] = None
    market_cap: Optional[float] = None
    avg_daily_volume: Optional[float] = None  # shares


@dataclass
class BasicEdgarSnapshot:
    revenue_ttm: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_income_ttm: Optional[float] = None
    free_cash_flow_ttm: Optional[float] = None
    cash: Optional[float] = None
    debt: Optional[float] = None
    shares_outstanding: Optional[float] = None
    going_concern_flag: Optional[bool] = None


def fmt_money(x: Optional[float]) -> str:
    if x is None:
        return "NA"
    if abs(x) >= 1e9:
        return f"${x/1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"${x/1e6:.2f}M"
    if abs(x) >= 1e3:
        return f"${x/1e3:.2f}K"
    return f"${x:.2f}"


def fmt_num(x: Optional[float]) -> str:
    return "NA" if x is None else f"{x:,.0f}"


def fmt_pct(x: Optional[float]) -> str:
    return "NA" if x is None else f"{x*100:.1f}%"


def fmt_yes_no_na(flag: Optional[bool]) -> str:
    if flag is True:
        return "Yes"
    if flag is False:
        return "No"
    return "NA"


def render_filled_scorecard(
    ticker: str,
    company: str | None,
    sector: str | None,
    industry: str | None,
    market: BasicMarketSnapshot,
    edgar: BasicEdgarSnapshot,
) -> str:
    scorecard = load_md("scorecard_v1.md")

    now = datetime.now().strftime("%Y-%m-%d")
    filled = scorecard
    filled = filled.replace("Ticker:", f"Ticker: {ticker}")
    filled = filled.replace("Company:", f"Company: {company or 'NA'}")
    filled = filled.replace("Sector:", f"Sector: {sector or 'NA'}")
    filled = filled.replace("Industry:", f"Industry: {industry or 'NA'}")
    filled = filled.replace("Price:", f"Price: {market.price if market.price is not None else 'NA'}")
    filled = filled.replace("Market Cap:", f"Market Cap: {fmt_money(market.market_cap)}")
    filled = filled.replace("Score Date:", f"Score Date: {now}")

    appendix = f"""
---

# Data Appendix (v1 Autofill)

## Market
- Price: {market.price if market.price is not None else 'NA'}
- Market Cap: {fmt_money(market.market_cap)}
- Avg Daily Volume (shares): {fmt_num(market.avg_daily_volume)}

## EDGAR
- Revenue (TTM): {fmt_money(edgar.revenue_ttm)}
- Gross Margin: {fmt_pct(edgar.gross_margin)}
- Operating Margin: {fmt_pct(edgar.operating_margin)}
- Net Income (TTM): {fmt_money(edgar.net_income_ttm)}
- Free Cash Flow (TTM): {fmt_money(edgar.free_cash_flow_ttm)}
- Cash: {fmt_money(edgar.cash)}
- Debt: {fmt_money(edgar.debt)}
- Shares Outstanding: {fmt_num(edgar.shares_outstanding)}
- Going Concern Flag: {fmt_yes_no_na(edgar.going_concern_flag)}
"""
    return filled + appendix


def main() -> None:
    import sys

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Usage:
    #   python scanner/dd_brain/generate_scorecard.py AAPL
    ticker = sys.argv[1].upper().strip() if len(sys.argv) > 1 else "AAPL"

    # Adapters (keep dd_brain clean)
    from scanner.market.snapshot import get_market_snapshot
    from scanner.edgar.snapshot import get_edgar_snapshot

    market = get_market_snapshot(ticker)
    edgar = get_edgar_snapshot(ticker)

    md = render_filled_scorecard(
        ticker=ticker,
        company=None,
        sector=None,
        industry=None,
        market=market,
        edgar=edgar,
    )

    out = REPORTS_DIR / f"{ticker}_{datetime.now().strftime('%Y-%m-%d')}.md"
    out.write_text(md, encoding="utf-8")
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
