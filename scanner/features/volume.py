from __future__ import annotations
import pandas as pd
import numpy as np

def volume_expansion(df: pd.DataFrame) -> dict:
    v = df["volume"].astype(float)
    dv = df["dollar_volume"].astype(float)
    v5 = v.tail(5).mean() if len(v) >= 5 else float("nan")
    v30 = v.tail(30).mean() if len(v) >= 30 else float("nan")
    dv5 = dv.tail(5).mean() if len(dv) >= 5 else float("nan")
    dv30 = dv.tail(30).mean() if len(dv) >= 30 else float("nan")
    return {
        "vol_ratio_5_30": (v5 / v30) if (v30 and np.isfinite(v30) and v30 > 0) else float("nan"),
        "dvol_ratio_5_30": (dv5 / dv30) if (dv30 and np.isfinite(dv30) and dv30 > 0) else float("nan"),
    }
