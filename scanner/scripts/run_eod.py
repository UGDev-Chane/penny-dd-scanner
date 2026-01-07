from __future__ import annotations
import argparse
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from scanner.storage.db import sqlite_upsert_daily_bars


import pandas as pd
from dotenv import load_dotenv

from scanner.storage.db import connect
from scanner.market.tiingo import TiingoClient
from scanner.edgar.client import EdgarClient
from scanner.edgar.parsers import cik_pad, recent_filings
from scanner.features.momentum import stacked_returns
from scanner.features.volume import volume_expansion
from scanner.scoring.scorecard import score_candidate
from scanner.signals.rules import generate_signal
from scanner.utils.hash import sha256_file
from scanner.dd_brain.openai_dd import dd_note_from_context

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--date", type=str, default=None, help="YYYY-MM-DD. Defaults to today.")
    p.add_argument("--config", type=str, default="config/config.yaml")
    p.add_argument("--db", type=str, default="data/scanner.sqlite")
    p.add_argument("--dd", action="store_true", help="Enable DD brain summaries for top candidates")
    return p.parse_args()

def main():
    load_dotenv()
    args = parse_args()
    run_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()

    # Minimal universe for MVP. Replace with your universe builder later.
    # Put a few symbols in config or a CSV once ready.
    universe = ["SOUN", "BBIG"]  # placeholder examples; replace

    con = connect(Path(args.db))
    cfg_hash = sha256_file(Path(args.config))

    # Pull last 60 calendar days of bars to cover 20 trading days.
    start = run_date - timedelta(days=75)
    end = run_date

    tiingo = TiingoClient()
    bars = tiingo.eod_prices(universe, start=start, end=end)
    if bars.empty:
        print("No bars returned. Check symbols and Tiingo key.")
        return

    # Store bars
    bars.to_sql(
    "daily_bars",
    con,
    if_exists="append",
    index=False,
    method=sqlite_upsert_daily_bars,
)


    # EDGAR client
    edgar = EdgarClient(user_agent=os.getenv("SEC_USER_AGENT", "penny-dd-scanner/0.1 (contact: you@example.com)"), max_rps=5.0)

    results = []
    for sym in universe:
        df = bars[bars["symbol"] == sym].sort_values("date")
        if len(df) < 25:
            continue

        mom = stacked_returns(df)
        vol = volume_expansion(df)

        # Gates (MVP placeholders)
        gates = {
            "liquidity_ok": float(df["dollar_volume"].tail(20).mean()) >= 5_000_000,
            "sec_current": True,  # wire to filings freshness once CIK mapping is in place
            "recent_dilution_risk": False,
            "earnings_anticipation_window": False,  # wire to earnings calendar provider
            "post_earnings_window": False,          # wire to earnings date delta
        }

        feats = {**mom, **vol}
        score = score_candidate(feats, gates)

        results.append({
            "symbol": sym,
            "date": run_date.isoformat(),
            "score_total": score.total,
            "setup_class": score.setup_class,
            "components": score.components,
            "features": feats,
            "gates": gates,
        })

    if not results:
        print("No candidates after basic data availability checks.")
        return

    df_out = pd.DataFrame(results).sort_values("score_total", ascending=False)

    outdir = Path("outputs")
    outdir.mkdir(parents=True, exist_ok=True)

    watchlist_path = outdir / f"watchlist_{run_date.isoformat()}.csv"
    df_out[["symbol","score_total","setup_class"]].to_csv(watchlist_path, index=False)

    # Generate signals
    sig_rows = []
    for r in results:
        risk = {"stop_loss_pct": 0.10, "take_profit_pct": 0.10}
        sigs = generate_signal(r["symbol"], r["date"], r["score_total"], r["setup_class"], risk)
        for s in sigs:
            sig_rows.append({
                "symbol": s.symbol,
                "date": s.date,
                "signal": s.signal,
                "rationale_json": json.dumps(s.rationale, sort_keys=True),
            })
    sig_df = pd.DataFrame(sig_rows)
    signals_path = outdir / f"signals_{run_date.isoformat()}.csv"
    sig_df.to_csv(signals_path, index=False)

    # Optional DD notes for top N
    if args.dd:
        top = df_out.head(10).to_dict(orient="records")
        for r in top:
            context = {
                "symbol": r["symbol"],
                "date": run_date.isoformat(),
                "score_total": r["score_total"],
                "setup_class": r["setup_class"],
                "components": r["components"],
                "features": results[[x["symbol"] for x in results].index(r["symbol"])]["features"] if True else {},
                "gates": results[[x["symbol"] for x in results].index(r["symbol"])]["gates"] if True else {},
            }
            note = dd_note_from_context(context)
            con.execute(
                "INSERT OR REPLACE INTO dd_notes(symbol,date,model,note_md) VALUES (?,?,?,?)",
                (r["symbol"], run_date.isoformat(), os.getenv("OPENAI_MODEL","gpt-5.2"), note),
            )
        con.commit()

    # Report
    report_path = outdir / f"report_{run_date.isoformat()}.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"# EOD Scan Report {run_date.isoformat()}\n\n")
        f.write("## Top candidates\n\n")
        f.write(df_out[["symbol","score_total","setup_class"]].head(20).to_markdown(index=False))
        f.write("\n\n")
        f.write("## Files\n")
        f.write(f"- {watchlist_path}\n")
        f.write(f"- {signals_path}\n")
        f.write(f"- {report_path}\n")

    print(f"Wrote {watchlist_path}")
    print(f"Wrote {signals_path}")
    print(f"Wrote {report_path}")

if __name__ == "__main__":
    import os
    main()
