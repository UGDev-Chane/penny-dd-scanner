from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Iterable

from .client import EdgarClient
from .parsers import cik_pad


@dataclass
class EdgarSnapshot:
    revenue_ttm: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_income_ttm: Optional[float] = None
    free_cash_flow_ttm: Optional[float] = None
    cash: Optional[float] = None
    debt: Optional[float] = None
    shares_outstanding: Optional[float] = None
    going_concern_flag: Optional[bool] = None  # v1: left as NA


_TICKER_CIK_CACHE: Optional[dict[str, str]] = None


def _require_user_agent() -> str:
    ua = os.getenv("SEC_USER_AGENT") or os.getenv("EDGAR_USER_AGENT")
    if not ua:
        raise RuntimeError("Missing SEC_USER_AGENT (or EDGAR_USER_AGENT). Set it in .env")
    return ua


def _load_ticker_cik_map(client: EdgarClient) -> dict[str, str]:
    """
    Loads SEC ticker-to-CIK mapping. Cached per process.
    Source is on www.sec.gov.
    """
    global _TICKER_CIK_CACHE
    if _TICKER_CIK_CACHE is not None:
        return _TICKER_CIK_CACHE

    data = client.get_json("/files/company_tickers.json", host="www")
    out: dict[str, str] = {}
    for _, row in data.items():
        t = str(row.get("ticker", "")).upper().strip()
        cik = cik_pad(str(row.get("cik_str", "")))
        if t and cik:
            out[t] = cik

    _TICKER_CIK_CACHE = out
    return out


def _facts_list(company_facts: dict, tag: str, unit: str) -> list[dict]:
    """
    Pull a list of fact entries for a us-gaap tag and unit.
    Returns [] if missing.
    """
    facts = company_facts.get("facts", {}).get("us-gaap", {})
    node = facts.get(tag, {})
    units = node.get("units", {})
    vals = units.get(unit, [])
    if not isinstance(vals, list):
        return []
    # Filter out malformed entries
    return [v for v in vals if isinstance(v, dict) and v.get("val") is not None and v.get("end")]


def _sort_by_end(items: Iterable[dict]) -> list[dict]:
    def key(x: dict) -> str:
        return str(x.get("end", ""))
    return sorted(list(items), key=key)


def _latest_value(items: list[dict]) -> Optional[float]:
    if not items:
        return None
    items = _sort_by_end(items)
    v = items[-1].get("val")
    try:
        return float(v)
    except Exception:
        return None


def _ttm_sum_quarters(items: list[dict]) -> Optional[float]:
    """
    Prefer summing last 4 quarterly values if present.
    Otherwise return None.
    """
    if not items:
        return None
    items = _sort_by_end(items)

    # Favor 10-Q entries
    q_items = [x for x in items if str(x.get("form", "")).upper() == "10-Q"]
    if len(q_items) >= 4:
        last4 = q_items[-4:]
        try:
            return float(sum(float(x["val"]) for x in last4))
        except Exception:
            return None

    return None


def _latest_annual(items: list[dict]) -> Optional[float]:
    """
    Best-effort annual fallback: most recent 10-K value.
    """
    if not items:
        return None
    items = _sort_by_end(items)
    k_items = [x for x in items if str(x.get("form", "")).upper() == "10-K"]
    if k_items:
        return _latest_value(k_items)
    # If no 10-K, just take latest
    return _latest_value(items)


def _ttm_or_annual(items: list[dict]) -> Optional[float]:
    ttm = _ttm_sum_quarters(items)
    if ttm is not None:
        return ttm
    return _latest_annual(items)


def get_edgar_snapshot(ticker: str) -> EdgarSnapshot:
    sym = ticker.upper().strip()
    client = EdgarClient(user_agent=_require_user_agent())

    mapping = _load_ticker_cik_map(client)
    cik10 = mapping.get(sym)
    if not cik10:
        return EdgarSnapshot()

    facts = client.company_facts(cik10)

    # Revenue: try common tags in order
    revenue_items = _facts_list(facts, "Revenues", "USD")
    if not revenue_items:
        revenue_items = _facts_list(facts, "SalesRevenueNet", "USD")
    revenue_ttm = _ttm_or_annual(revenue_items)

    net_income_items = _facts_list(facts, "NetIncomeLoss", "USD")
    net_income_ttm = _ttm_or_annual(net_income_items)

    gross_profit_items = _facts_list(facts, "GrossProfit", "USD")
    gross_profit_ttm = _ttm_or_annual(gross_profit_items)

    op_income_items = _facts_list(facts, "OperatingIncomeLoss", "USD")
    op_income_ttm = _ttm_or_annual(op_income_items)

    # Cash and debt: latest point-in-time values
    cash_items = _facts_list(facts, "CashAndCashEquivalentsAtCarryingValue", "USD")
    if not cash_items:
        cash_items = _facts_list(facts, "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "USD")
    cash = _latest_value(cash_items)

    debt = None
    debt_items = _facts_list(facts, "Debt", "USD")
    if debt_items:
        debt = _latest_value(debt_items)
    else:
        # Try summing common components if Debt isn't present
        ltd_current = _latest_value(_facts_list(facts, "LongTermDebtCurrent", "USD"))
        ltd_noncurrent = _latest_value(_facts_list(facts, "LongTermDebtNoncurrent", "USD"))
        if ltd_current is not None or ltd_noncurrent is not None:
            debt = float(ltd_current or 0.0) + float(ltd_noncurrent or 0.0)

    shares_items = _facts_list(facts, "CommonStockSharesOutstanding", "shares")
    shares_outstanding = _latest_value(shares_items)

    # FCF: CFO - CapEx (best-effort)
    cfo_items = _facts_list(facts, "NetCashProvidedByUsedInOperatingActivities", "USD")
    capex_items = _facts_list(facts, "PaymentsToAcquirePropertyPlantAndEquipment", "USD")
    cfo_ttm = _ttm_or_annual(cfo_items)
    capex_ttm = _ttm_or_annual(capex_items)
    free_cash_flow_ttm = None
    if cfo_ttm is not None and capex_ttm is not None:
        free_cash_flow_ttm = float(cfo_ttm) - float(capex_ttm)

    gross_margin = None
    operating_margin = None
    if revenue_ttm and revenue_ttm != 0:
        if gross_profit_ttm is not None:
            gross_margin = float(gross_profit_ttm) / float(revenue_ttm)
        if op_income_ttm is not None:
            operating_margin = float(op_income_ttm) / float(revenue_ttm)

    return EdgarSnapshot(
        revenue_ttm=revenue_ttm,
        gross_margin=gross_margin,
        operating_margin=operating_margin,
        net_income_ttm=net_income_ttm,
        free_cash_flow_ttm=free_cash_flow_ttm,
        cash=cash,
        debt=debt,
        shares_outstanding=shares_outstanding,
        going_concern_flag=None,  # v1: we add text-scan later
    )
