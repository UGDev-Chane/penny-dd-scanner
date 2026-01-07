from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Signal:
    symbol: str
    date: str
    signal: str
    rationale: dict

def generate_signal(symbol: str, date: str, score_total: float, setup_class: str, risk: dict) -> list[Signal]:
    # EOD signal generation. Human approves.
    # This is intentionally conservative for v1.
    signals: list[Signal] = []
    if setup_class in ("earnings_anticipation", "post_earnings_continuation") and score_total >= 70:
        signals.append(Signal(symbol, date, "WATCH_ENTER", {
            "score": score_total,
            "setup": setup_class,
            "risk": risk,
            "note": "Candidate meets threshold. Review DD notes before entry.",
        }))
    return signals
