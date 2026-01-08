from __future__ import annotations

import time
from dataclasses import dataclass

import requests

SEC_DATA = "https://data.sec.gov"
SEC_ARCHIVES = "https://www.sec.gov/Archives"


@dataclass
class EdgarClient:
    user_agent: str
    max_rps: float = 5.0

    def __post_init__(self):
        self.s = requests.Session()
        # Let requests set the Host header automatically based on the URL.
        self.s.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )
        self._min_interval = 1.0 / max(self.max_rps, 0.1)
        self._last = 0.0

    def _throttle(self) -> None:
        now = time.time()
        wait = self._min_interval - (now - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

    def get_json(self, path: str, host: str = "data") -> dict:
        """
        host:
          - "data" -> https://data.sec.gov
          - otherwise -> https://www.sec.gov
        """
        self._throttle()

        if host == "data":
            url = f"{SEC_DATA}{path}"
        else:
            url = f"https://www.sec.gov{path}"

        r = self.s.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    def company_submissions(self, cik10: str) -> dict:
        # cik10 should be zero-padded 10 digits
        return self.get_json(f"/submissions/CIK{cik10}.json", host="data")

    def company_facts(self, cik10: str) -> dict:
        return self.get_json(f"/api/xbrl/companyfacts/CIK{cik10}.json", host="data")
