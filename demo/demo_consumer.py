#!/usr/bin/env python3
"""Local-only reviewer demo: evidence decisions gate simulated actions.

This script imports the existing evidence service and serves it only on a
random localhost port with fixed public-market-shaped snapshots. It has no
account, credential, order, wallet, or production-network capability.
"""

from __future__ import annotations

import copy
import json
import sys
import threading
from pathlib import Path
from urllib.request import Request, urlopen

PROBE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROBE_DIR))

import evidence_api  # noqa: E402


def fixed_snapshot(*, quote_age_ms: int) -> dict:
    exchange_ts_ms = 1_800_000_000_000
    return {
        "metadata": {
            "instId": "BTC-USDT",
            "instType": "SPOT",
            "state": "live",
            "quoteCcy": "USDT",
            "tickSz": "0.1",
            "lotSz": "0.00001",
            "minSz": "0.00001",
        },
        "book": {
            "ts": str(exchange_ts_ms),
            "bids": [["99990", "1"]],
            "asks": [["100000", "1"]],
        },
        "sources": ["LOCAL_FIXED_REVIEWER_FIXTURE"],
        "received_at_ms": exchange_ts_ms + quote_age_ms,
    }


class FixedClient:
    snapshot_value: dict = {}

    def snapshot(self, instrument: str) -> dict:
        assert instrument == "BTC-USDT"
        return copy.deepcopy(self.snapshot_value)


def invoke_local_service(snapshot: dict) -> dict:
    FixedClient.snapshot_value = snapshot
    original_client = evidence_api.OKXPublicClient
    evidence_api.OKXPublicClient = FixedClient
    server = evidence_api.ThreadingHTTPServer(("127.0.0.1", 0), evidence_api.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = json.dumps(
            {"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000}
        ).encode()
        request = Request(
            f"http://127.0.0.1:{server.server_port}/v1/evidence/check",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return json.load(response)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        evidence_api.OKXPublicClient = original_client


def run_case(name: str, quote_age_ms: int) -> None:
    print(f"CASE={name} INTENDED_SIMULATED_ORDER=BUY BTC-USDT 1000_USDT")
    result = invoke_local_service(fixed_snapshot(quote_age_ms=quote_age_ms))
    summary = {
        "mode": "LOCAL_FIXED_REVIEWER_FIXTURE",
        "decision": result["decision"],
        "reason_codes": result["reason_codes"],
        "quote_age_ms": result["policy_checks"]["quote_age"]["actual_ms"],
        "spread_bps": result["market_evidence"]["spread_bps"],
        "estimated_cost_bps": result["execution_cost"]["estimated_one_way_cost_bps"],
        "vwap": result["execution_cost"]["executable_price_vwap"],
        "policy_version": result["policy_version"],
    }
    print("EVIDENCE=" + json.dumps(summary, separators=(",", ":")))
    if result["decision"] == "GO":
        print("ACTION_ALLOWED_SIMULATION_ONLY")
    else:
        print("ACTION_ABORTED")


def main() -> None:
    run_case("STALE_QUOTE_REJECT", quote_age_ms=10_000)
    run_case("FRESH_QUOTE_GO", quote_age_ms=100)


if __name__ == "__main__":
    main()
