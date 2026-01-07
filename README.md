# penny-dd-scanner (local EOD)

Local, end-of-day scanner focused on:
- Earnings anticipation runners
- Post-earnings continuation

Data sources:
- Tiingo (EOD bars)
- SEC EDGAR (filings metadata + company facts)

This repo is an MVP scaffold. It stores history in SQLite and emits daily outputs (CSV + markdown).

## Quick start

1) Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Copy env template and fill values:

```bash
cp .env.example .env
```

3) Initialize DB:

```bash
python -m scanner.scripts.init_db
```

4) Run EOD scan:

```bash
python -m scanner.scripts.run_eod --date 2026-01-06
```

Outputs:
- outputs/watchlist_YYYY-MM-DD.csv
- outputs/signals_YYYY-MM-DD.csv
- outputs/report_YYYY-MM-DD.md

## Notes
- SEC requests are rate-limited. Keep it that way.
- This system is decision support. You approve trades.
