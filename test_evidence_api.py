from __future__ import annotations

import copy
import http.client
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evidence_api
from evidence_api import Handler, POLICY_VERSION, UpstreamError, deterministic_report, evaluate, validate_request


def snapshot(*, ts=1_800_000_000_000, asks=None, bids=None):
    return {
        "metadata": {"instId": "BTC-USDT", "instType": "SPOT", "state": "live",
                     "quoteCcy": "USDT", "tickSz": "0.1", "lotSz": "0.00001", "minSz": "0.00001"},
        "book": {"ts": str(ts), "bids": bids or [["99990", "1"]],
                 "asks": asks or [["100000", "1"]]},
        "sources": ["https://www.okx.com/api/v5/public/instruments", "https://www.okx.com/api/v5/market/books"],
        "received_at_ms": ts + 100,
    }


class FakeClient:
    def __init__(self, value=None, error=None): self.value, self.error = value, error
    def snapshot(self, instrument):
        if self.error: raise self.error
        return copy.deepcopy(self.value)


def post(body: bytes, *, content_length: int | None = None):
    server = evidence_api.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        headers = {"Content-Type": "application/json"}
        if content_length is not None:
            headers["Content-Length"] = str(content_length)
        connection.request("POST", "/v1/evidence/check", body=body, headers=headers)
        response = connection.getresponse()
        return response.status, __import__("json").loads(response.read())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_fixed_snapshot_is_deterministic_except_response_metadata():
    req = validate_request({"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000})
    first = deterministic_report(req, snapshot())
    second = deterministic_report(req, snapshot())
    assert first == second
    assert first["evidence_hash"] == second["evidence_hash"]
    assert first["policy_version"] == POLICY_VERSION


def test_complete_live_check_returns_structured_result():
    status, body = evaluate({"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000}, FakeClient(snapshot()))
    assert status == 200 and body["report_status"] == "COMPLETE"
    assert body["decision"] in {"GO", "REJECT"}
    assert body["mode"] == "live_public"
    assert body["execution_cost"]["vwap_is_snapshot_estimate"] is True


def test_omitted_max_cost_uses_policy_default():
    status, body = evaluate(
        {"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000},
        FakeClient(snapshot()),
    )
    assert status == 200
    assert body["policy_checks"]["estimated_cost"]["threshold_bps"] == 30.0


def test_tighter_max_cost_can_reject():
    status, body = evaluate(
        {"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000, "max_cost_bps": 10},
        FakeClient(snapshot()),
    )
    assert status == 200 and body["decision"] == "REJECT"
    assert body["policy_checks"]["estimated_cost"] == {
        "threshold_bps": 10.0,
        "actual_bps": pytest.approx(12.500025001251014),
        "passed": False,
    }
    assert body["reason_codes"] == ["ESTIMATED_COST_EXCEEDS_POLICY"]


def test_looser_max_cost_only_changes_cost_threshold():
    payload = {"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000}
    default_status, default = evaluate(payload, FakeClient(snapshot()))
    loose_status, loose = evaluate({**payload, "max_cost_bps": 100}, FakeClient(snapshot()))

    assert default_status == loose_status == 200
    assert loose["policy_checks"]["estimated_cost"]["threshold_bps"] == 100.0
    for field in ("market_evidence", "execution_cost", "instrument_metadata", "data_quality"):
        assert loose[field] == default[field]
    for check in ("quote_age", "spread", "depth"):
        assert loose["policy_checks"][check] == default["policy_checks"][check]


@pytest.mark.parametrize("value", [True, "30", -1, 1000.1, float("inf"), float("nan")])
def test_invalid_max_cost_fails_closed(value):
    status, body = evaluate(
        {"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000, "max_cost_bps": value},
        FakeClient(snapshot()),
    )
    assert status == 400 and body["decision"] == "REJECT"
    assert body["report_status"] == "REJECTED_INPUT"


@pytest.mark.parametrize("payload", [
    {},
    {"instrument": "BTC-USDT", "side": "hold", "notional_usdt": 10},
    {"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 0},
    {"instrument": "btc-usdt", "side": "buy", "notional_usdt": 10},
])
def test_invalid_input_is_rejected(payload):
    status, body = evaluate(payload, FakeClient(snapshot()))
    assert status == 400 and body["decision"] == "REJECT"
    assert body["report_status"] == "REJECTED_INPUT"


def test_stale_quote_can_never_go():
    stale = snapshot()
    stale["received_at_ms"] += 10_000
    status, body = evaluate({"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000}, FakeClient(stale))
    assert status == 200 and body["decision"] == "REJECT"
    assert "STALE_QUOTE" in body["reason_codes"]


def test_insufficient_depth_can_never_go():
    shallow = snapshot(asks=[["100000", "0.0001"]])
    status, body = evaluate({"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000}, FakeClient(shallow))
    assert status == 200 and body["decision"] == "REJECT"
    assert "INSUFFICIENT_DISPLAYED_DEPTH" in body["reason_codes"]


def test_upstream_failure_is_not_a_successful_report():
    status, body = evaluate({"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 1000}, FakeClient(error=UpstreamError("timeout")))
    assert status == 502 and body["decision"] == "WATCH"
    assert body["report_status"] == "TECHNICAL_FAILURE"


def test_unsupported_inverse_contract_rejected():
    inverse = snapshot()
    inverse["metadata"].update({"instId": "BTC-USD-SWAP", "instType": "SWAP", "ctType": "inverse", "settleCcy": "BTC"})
    status, body = evaluate({"instrument": "BTC-USD-SWAP", "side": "buy", "notional_usdt": 1000}, FakeClient(inverse))
    assert status == 400 and body["decision"] == "REJECT"


def test_linear_swap_uses_contract_value_and_lot_size():
    linear = snapshot()
    linear["metadata"].update({"instId": "BTC-USDT-SWAP", "instType": "SWAP", "ctType": "linear",
                               "settleCcy": "USDT", "ctVal": "0.01", "ctValCcy": "BTC",
                               "lotSz": "1", "minSz": "1"})
    linear["book"].update({"bids": [["99990", "100"]], "asks": [["100000", "100"]]})
    status, body = evaluate({"instrument": "BTC-USDT-SWAP", "side": "buy", "notional_usdt": 2500}, FakeClient(linear))
    assert status == 200
    assert body["execution_cost"]["lot_aligned_quantity"] == 2
    assert body["execution_cost"]["quantity_unit"] == "CONTRACTS"
    assert body["execution_cost"]["filled_notional_usdt"] == pytest.approx(2000)


def test_notional_below_minimum_size_rejected():
    status, body = evaluate({"instrument": "BTC-USDT", "side": "buy", "notional_usdt": 0.1}, FakeClient(snapshot()))
    assert status == 400 and "NOTIONAL_BELOW_MINIMUM_SIZE" in body["reason_codes"]


def test_empty_object_requests_all_a2mcp_required_fields():
    status, body = post(b"{}")
    fields = body["input_required"]["fields"]
    assert status == 400 and body["status"] == "input_required"
    assert body["input_required"]["method"] == "POST"
    assert [(field["name"], field["type"], field["carrier"]) for field in fields] == [
        ("instrument", "string", "body"),
        ("side", "string", "body"),
        ("notional_usdt", "number", "body"),
        ("max_cost_bps", "number", "body"),
    ]
    assert fields[-1]["required"] is True
    assert "range 0-1000" in fields[-1]["description"]
    assert "use 30" in fields[-1]["description"]


def test_partial_object_requests_only_missing_field():
    status, body = post(b'{"instrument":"BTC-USDT-SWAP","side":"buy"}')
    assert status == 400
    assert [field["name"] for field in body["input_required"]["fields"]] == [
        "notional_usdt",
        "max_cost_bps",
    ]


def test_complete_legacy_request_does_not_require_max_cost():
    expected = {"report_status": "COMPLETE", "decision": "GO", "sentinel": "legacy-default"}
    original = evidence_api.evaluate
    evidence_api.evaluate = lambda payload: (200, expected)
    try:
        status, body = post(b'{"instrument":"BTC-USDT-SWAP","side":"buy","notional_usdt":1000}')
    finally:
        evidence_api.evaluate = original
    assert status == 200 and body == expected


def test_complete_request_still_uses_existing_engine(monkeypatch):
    expected = {"report_status": "COMPLETE", "decision": "REJECT", "sentinel": "existing-engine"}
    monkeypatch.setattr(evidence_api, "evaluate", lambda payload: (200, expected))
    status, body = post(b'{"instrument":"BTC-USDT-SWAP","side":"buy","notional_usdt":1000}')
    assert status == 200 and body == expected


def test_malformed_json_still_fails_closed():
    status, body = post(b'{"instrument":')
    assert status == 400 and body["report_status"] == "REJECTED_INPUT"


def test_oversized_body_still_fails_closed():
    status, body = post(b"{}", content_length=evidence_api.MAX_REQUEST_BODY_BYTES + 1)
    assert status == 400 and body["reason_codes"] == ["request body size is invalid"]
