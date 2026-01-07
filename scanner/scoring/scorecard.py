from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class ScoreResult:
    total: float
    setup_class: str
    components: dict

def score_candidate(features: dict, gates: dict) -> ScoreResult:
    # Deterministic, auditable scoring.
    # features: momentum, volume, liquidity, edgar flags, earnings window flags
    # gates: pass/fail gates and reasons

    comps: Dict[str, float] = {}
    total = 0.0

    # Liquidity weight
    liq = 0.0
    if gates.get("liquidity_ok"):
        liq = 25.0
    comps["liquidity"] = liq
    total += liq

    # Momentum weight
    mom = 0.0
    r5 = features.get("ret_5d")
    r10 = features.get("ret_10d")
    r20 = features.get("ret_20d")
    accel = features.get("accel")
    if isinstance(accel, bool) and accel and r5 and r10 and r20:
        mom = 25.0
    elif r5 is not None and r5 > 0:
        mom = 15.0
    comps["momentum"] = mom
    total += mom

    # Volume confirmation
    vol = 0.0
    vr = features.get("dvol_ratio_5_30")
    if vr is not None and vr == vr and vr >= 2.0:
        vol = 20.0
    elif vr is not None and vr == vr and vr >= 1.5:
        vol = 12.0
    comps["volume"] = vol
    total += vol

    # Dilution penalty
    dil = 0.0
    if gates.get("recent_dilution_risk"):
        dil = -20.0
    comps["dilution_penalty"] = dil
    total += dil

    # Filings freshness
    sec = 0.0
    if gates.get("sec_current"):
        sec = 10.0
    else:
        sec = -50.0
    comps["sec_filer"] = sec
    total += sec

    # Setup classification
    if gates.get("earnings_anticipation_window"):
        setup = "earnings_anticipation"
        total += 10.0
        comps["setup_bonus"] = 10.0
    elif gates.get("post_earnings_window"):
        setup = "post_earnings_continuation"
        total += 10.0
        comps["setup_bonus"] = 10.0
    else:
        setup = "none"
        comps["setup_bonus"] = 0.0

    return ScoreResult(total=total, setup_class=setup, components=comps)
