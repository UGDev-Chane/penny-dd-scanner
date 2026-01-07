from __future__ import annotations
import pandas as pd
import numpy as np

def stacked_returns(df: pd.DataFrame) -> dict:
    # df: rows sorted by date ascending with 'close'
    closes = df["close"].astype(float).to_numpy()
    def ret(n: int) -> float:
        if len(closes) <= n:
            return float("nan")
        return (closes[-1] / closes[-(n+1)]) - 1.0
    r5 = ret(5)
    r10 = ret(10)
    r20 = ret(20)
    accel = float("nan")
    if np.isfinite(r5) and np.isfinite(r10) and np.isfinite(r20):
        accel = (r5 > r10) and (r10 > r20)
    return {"ret_5d": r5, "ret_10d": r10, "ret_20d": r20, "accel": accel}
