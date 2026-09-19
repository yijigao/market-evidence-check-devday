#!/usr/bin/env python3
"""Free, public-data-only Market Evidence Agent HTTP service.

This module has no account, credential, wallet, payment, or order capability.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlencode

import requests

SCHEMA_VERSION = "1.0"
POLICY_VERSION = "2026-09-17.1"
OKX_BASE_URL = os.environ.get("OKX_PUBLIC_BASE_URL", "https://www.okx.com")
POLICY = {
    "max_quote_age_ms": 500,
    "max_spread_bps": 20.0,
    "max_estimated_cost_bps": 30.0,
    "default_taker_fee_bps": 10.0,
    "default_slippage_buffer_bps": 2.0,
    "book_depth": 400,
}
ALLOWED_SIDES = {"buy", "sell"}
MAX_NOTIONAL_USDT = 1_000_000.0
MAX_REQUEST_BODY_BYTES = 16_384
REQUIRED_INPUT_FIELDS = (
    {"name": "instrument", "type": "string", "required": True, "carrier": "body"},
    {"name": "side", "type": "string", "required": True, "carrier": "body"},
    {"name": "notional_usdt", "type": "number", "required": True, "carrier": "body"},
)


class InputError(ValueError):
    pass


class UpstreamError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidatedRequest:
    instrument: str
    side: str
    notional_usdt: float
    taker_fee_bps: float
    slippage_buffer_bps: float
    fee_source: str
    slippage_source: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def input_required(payload: Any) -> dict[str, Any] | None:
    """Return the installed A2MCP contract for missing required body fields."""
    if not isinstance(payload, dict):
        return None
    missing = [field for field in REQUIRED_INPUT_FIELDS if field["name"] not in payload]
    if not missing:
        return None
    return {
        "status": "input_required",
        "input_required": {
            "method": "POST",
            "message": "Required request body fields are missing",
            "fields": missing,
        },
    }


def validate_request(payload: Any) -> ValidatedRequest:
    if not isinstance(payload, dict):
        raise InputError("request body must be a JSON object")
    allowed = {"instrument", "side", "notional_usdt", "cost_assumptions"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise InputError(f"unknown fields: {', '.join(unknown)}")
    instrument = payload.get("instrument")
    side = payload.get("side")
    notional = payload.get("notional_usdt")
    if not isinstance(instrument, str) or not instrument or len(instrument) > 64:
        raise InputError("instrument must be a non-empty string up to 64 characters")
    if not all(c.isupper() or c.isdigit() or c == "-" for c in instrument):
        raise InputError("instrument contains unsupported characters")
    if side not in ALLOWED_SIDES:
        raise InputError("side must be 'buy' or 'sell'")
    if isinstance(notional, bool) or not isinstance(notional, (int, float)):
        raise InputError("notional_usdt must be numeric")
    notional = float(notional)
    if not math.isfinite(notional) or not 0 < notional <= MAX_NOTIONAL_USDT:
        raise InputError(f"notional_usdt must be within (0, {MAX_NOTIONAL_USDT:g}]")

    costs = payload.get("cost_assumptions") or {}
    if not isinstance(costs, dict):
        raise InputError("cost_assumptions must be an object")
    unknown_costs = sorted(set(costs) - {"taker_fee_bps", "slippage_buffer_bps"})
    if unknown_costs:
        raise InputError(f"unknown cost fields: {', '.join(unknown_costs)}")

    def cost(name: str, default: float) -> tuple[float, str]:
        supplied = name in costs
        value = costs.get(name, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InputError(f"{name} must be numeric")
        value = float(value)
        if not math.isfinite(value) or not 0 <= value <= 1000:
            raise InputError(f"{name} must be within [0, 1000]")
        return value, "CALLER_ASSUMPTION" if supplied else "POLICY_DEFAULT_ASSUMPTION"

    fee, fee_source = cost("taker_fee_bps", POLICY["default_taker_fee_bps"])
    slip, slip_source = cost("slippage_buffer_bps", POLICY["default_slippage_buffer_bps"])
    return ValidatedRequest(instrument, side, notional, fee, slip, fee_source, slip_source)


class OKXPublicClient:
    def __init__(self, base_url: str = OKX_BASE_URL, timeout_seconds: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get(self, path: str, params: dict[str, str]) -> tuple[list[Any], str]:
        url = f"{self.base_url}{path}?{urlencode(params)}"
        try:
            response = self.session.get(
                url,
                headers={"User-Agent": "AMZWatch-Market-Evidence/1.0"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise UpstreamError(f"OKX public request failed: {type(exc).__name__}") from exc
        if body.get("code") != "0" or not isinstance(body.get("data"), list):
            raise UpstreamError(f"OKX public response code {body.get('code', 'UNKNOWN')}")
        return body["data"], url

    def snapshot(self, instrument: str) -> dict[str, Any]:
        inst_type = "SWAP" if instrument.endswith("-SWAP") else "SPOT"
        instruments, metadata_url = self.get(
            "/api/v5/public/instruments", {"instType": inst_type, "instId": instrument}
        )
        books, book_url = self.get(
            "/api/v5/market/books", {"instId": instrument, "sz": str(POLICY["book_depth"])}
        )
        if len(instruments) != 1:
            raise UpstreamError("instrument metadata missing or ambiguous")
        if len(books) != 1:
            raise UpstreamError("order book snapshot missing or ambiguous")
        return {
            "metadata": instruments[0],
            "book": books[0],
            "sources": [metadata_url, book_url],
            "received_at_ms": int(time.time() * 1000),
        }


def verified_multiplier(metadata: dict[str, Any]) -> tuple[float, str]:
    inst_type = metadata.get("instType")
    if inst_type == "SPOT":
        if metadata.get("quoteCcy") != "USDT":
            raise InputError("UNSUPPORTED_QUOTE_CURRENCY")
        return 1.0, "SPOT_BASE_UNITS"
    if inst_type == "SWAP":
        if metadata.get("ctType") != "linear" or metadata.get("settleCcy") != "USDT":
            raise InputError("UNSUPPORTED_CONTRACT_TYPE")
        try:
            multiplier = float(metadata["ctVal"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InputError("UNVERIFIED_CONTRACT_VALUE") from exc
        if not math.isfinite(multiplier) or multiplier <= 0:
            raise InputError("UNVERIFIED_CONTRACT_VALUE")
        return multiplier, "LINEAR_SWAP_CTVAL_BASE_UNITS"
    raise InputError("UNSUPPORTED_INSTRUMENT_TYPE")


def executable_quantity(metadata: dict[str, Any], notional: float, mid: float, multiplier: float) -> tuple[float, float]:
    """Convert USDT notional to a valid lot-aligned book quantity."""
    try:
        lot = Decimal(str(metadata["lotSz"]))
        minimum = Decimal(str(metadata["minSz"]))
        raw = Decimal(str(notional)) / (Decimal(str(mid)) * Decimal(str(multiplier)))
    except (KeyError, InvalidOperation, TypeError, ValueError, ZeroDivisionError) as exc:
        raise InputError("UNVERIFIED_SIZE_METADATA") from exc
    if lot <= 0 or minimum <= 0:
        raise InputError("UNVERIFIED_SIZE_METADATA")
    quantity = (raw / lot).to_integral_value(rounding=ROUND_FLOOR) * lot
    if quantity < minimum or quantity <= 0:
        raise InputError("NOTIONAL_BELOW_MINIMUM_SIZE")
    return float(quantity), float(quantity * Decimal(str(mid)) * Decimal(str(multiplier)))


def quantity_vwap(levels: list[Any], quantity: float, multiplier: float) -> tuple[float | None, float, float, bool, int]:
    remaining, cash, filled, used = quantity, 0.0, 0.0, 0
    for level in levels:
        try:
            price, available = float(level[0]), float(level[1])
        except (IndexError, TypeError, ValueError):
            continue
        if price <= 0 or available <= 0:
            continue
        take = min(remaining, available)
        cash += take * price * multiplier
        filled += take
        remaining -= take
        used += 1
        if remaining <= max(quantity * 1e-12, 1e-12):
            break
    complete = remaining <= max(quantity * 1e-12, 1e-12)
    return (cash / (filled * multiplier) if filled else None, filled, cash, complete, used)


def deterministic_report(request: ValidatedRequest, snapshot: dict[str, Any]) -> dict[str, Any]:
    metadata, book = snapshot["metadata"], snapshot["book"]
    if metadata.get("instId") != request.instrument or metadata.get("state") != "live":
        raise InputError("INSTRUMENT_NOT_LIVE")
    multiplier, conversion = verified_multiplier(metadata)
    try:
        bid = float(book["bids"][0][0])
        ask = float(book["asks"][0][0])
        exchange_ts_ms = int(book["ts"])
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise UpstreamError("critical order book fields missing") from exc
    if not (0 < bid <= ask and math.isfinite(bid) and math.isfinite(ask)):
        raise UpstreamError("invalid or crossed public order book")

    mid = (bid + ask) / 2
    spread_bps = (ask / bid - 1) * 10_000
    quantity, target_notional_at_mid = executable_quantity(metadata, request.notional_usdt, mid, multiplier)
    levels = book["asks"] if request.side == "buy" else book["bids"]
    executable_price, filled_quantity, filled_notional, fill_complete, levels_used = quantity_vwap(
        levels, quantity, multiplier
    )
    impact_bps = None
    if executable_price is not None:
        impact_bps = ((executable_price / mid - 1) if request.side == "buy" else (mid / executable_price - 1)) * 10_000
        impact_bps = max(0.0, impact_bps)
    estimated_cost_bps = None if impact_bps is None else request.taker_fee_bps + request.slippage_buffer_bps + impact_bps
    quote_age_ms = max(0, snapshot["received_at_ms"] - exchange_ts_ms)

    checks = {
        "quote_age": {"threshold_ms": POLICY["max_quote_age_ms"], "actual_ms": quote_age_ms,
                      "passed": quote_age_ms <= POLICY["max_quote_age_ms"]},
        "spread": {"threshold_bps": POLICY["max_spread_bps"], "actual_bps": spread_bps,
                   "passed": spread_bps <= POLICY["max_spread_bps"]},
        "depth": {"requested_notional_usdt": request.notional_usdt,
                  "lot_aligned_target_notional_usdt": target_notional_at_mid,
                  "filled_notional_usdt": filled_notional, "passed": fill_complete},
        "estimated_cost": {"threshold_bps": POLICY["max_estimated_cost_bps"],
                           "actual_bps": estimated_cost_bps,
                           "passed": estimated_cost_bps is not None and estimated_cost_bps <= POLICY["max_estimated_cost_bps"]},
    }
    reasons = []
    if not checks["quote_age"]["passed"]: reasons.append("STALE_QUOTE")
    if not checks["spread"]["passed"]: reasons.append("SPREAD_EXCEEDS_POLICY")
    if not checks["depth"]["passed"]: reasons.append("INSUFFICIENT_DISPLAYED_DEPTH")
    if not checks["estimated_cost"]["passed"]: reasons.append("ESTIMATED_COST_EXCEEDS_POLICY")
    decision = "GO" if not reasons else "REJECT"

    evidence_core = {
        "schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "mode": "live_public",
        "input": {"instrument": request.instrument, "side": request.side,
                  "notional_usdt": request.notional_usdt},
        "instrument_metadata": {k: metadata.get(k) for k in
            ("instId", "instType", "state", "tickSz", "lotSz", "minSz", "ctType", "ctVal", "ctValCcy", "settleCcy")},
        "market_evidence": {"exchange_timestamp_ms": exchange_ts_ms, "received_timestamp_ms": snapshot["received_at_ms"],
                            "best_bid": bid, "best_ask": ask, "mid": mid, "spread_bps": spread_bps,
                            "book_levels_returned": {"bids": len(book["bids"]), "asks": len(book["asks"])},
                            "conversion": conversion},
        "execution_cost": {"executable_price_vwap": executable_price, "vwap_is_snapshot_estimate": True,
                           "lot_aligned_quantity": quantity, "quantity_unit": "BASE" if metadata.get("instType") == "SPOT" else "CONTRACTS",
                           "filled_quantity": filled_quantity, "filled_notional_usdt": filled_notional,
                           "complete": fill_complete, "levels_used": levels_used,
                           "price_impact_bps": impact_bps, "taker_fee_bps": request.taker_fee_bps,
                           "taker_fee_source": request.fee_source, "slippage_buffer_bps": request.slippage_buffer_bps,
                           "slippage_source": request.slippage_source, "estimated_one_way_cost_bps": estimated_cost_bps},
        "policy_checks": checks,
        "decision": decision,
        "reason_codes": reasons or ["ALL_DECLARED_CHECKS_PASSED"],
        "data_quality": {"critical_fields_complete": True, "quote_fresh": checks["quote_age"]["passed"],
                         "source": "OKX_PUBLIC_REST", "sources": snapshot["sources"]},
        "unverified_assumptions": ["taker fee is not an account-observed fee",
                                   "VWAP is a public snapshot estimate, not a guaranteed fill",
                                   "GO does not indicate alpha, profitability, safety, or trading authorization"],
    }
    canonical = json.dumps(evidence_core, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    evidence_core["evidence_hash"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
    return evidence_core


def evaluate(payload: Any, client: OKXPublicClient | None = None) -> tuple[int, dict[str, Any]]:
    checked_at = utc_now()
    request_id = str(uuid.uuid4())
    try:
        validated = validate_request(payload)
        snapshot = (client or OKXPublicClient()).snapshot(validated.instrument)
        report = deterministic_report(validated, snapshot)
        report.update({"request_id": request_id, "checked_at_utc": checked_at, "report_status": "COMPLETE"})
        return 200, report
    except InputError as exc:
        return 400, {"schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION,
                     "request_id": request_id, "checked_at_utc": checked_at,
                     "report_status": "REJECTED_INPUT", "decision": "REJECT",
                     "reason_codes": [str(exc)], "market_evidence": None, "execution_cost": None}
    except UpstreamError as exc:
        return 502, {"schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION,
                     "request_id": request_id, "checked_at_utc": checked_at,
                     "report_status": "TECHNICAL_FAILURE", "decision": "WATCH",
                     "reason_codes": ["UPSTREAM_DATA_UNAVAILABLE"], "detail": str(exc),
                     "market_evidence": None, "execution_cost": None}


class Handler(BaseHTTPRequestHandler):
    server_version = "MarketEvidence/1.0"

    def _json(self, status: int, body: dict[str, Any]):
        encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/__devday_healthz":
            self._json(200, {"status": "ok", "purpose": "prebuild-infrastructure"})
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/v1/evidence/check":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_REQUEST_BODY_BYTES:
                raise InputError("request body size is invalid")
            payload = {} if length == 0 else json.loads(self.rfile.read(length))
            required = input_required(payload)
            if required is not None:
                status, body = 400, required
            else:
                status, body = evaluate(payload)
        except (ValueError, json.JSONDecodeError, InputError) as exc:
            status, body = 400, {"report_status": "REJECTED_INPUT", "decision": "REJECT",
                                 "reason_codes": [str(exc)]}
        self._json(status, body)

    def log_message(self, fmt, *args):
        print(f"{self.log_date_time_string()} {self.client_address[0]} {fmt % args}", flush=True)


def main():
    host = os.environ.get("EVIDENCE_API_HOST", "127.0.0.1")
    port = int(os.environ.get("EVIDENCE_API_PORT", "18090"))
    print(f"Market Evidence Agent listening on {host}:{port}; public-data-only", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
