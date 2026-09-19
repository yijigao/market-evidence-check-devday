# Isolated caller demo output

- Run time: `2026-09-19T10:06:17Z`
- Mode: `LOCAL_FIXED_REVIEWER_FIXTURE`
- Network scope: localhost only
- Safety: simulation only; no account, API key, order, wallet, or production
  trading access

## Stale quote

```text
CASE=STALE_QUOTE_REJECT INTENDED_SIMULATED_ORDER=BUY BTC-USDT 1000_USDT
EVIDENCE={"mode":"LOCAL_FIXED_REVIEWER_FIXTURE","decision":"REJECT","reason_codes":["STALE_QUOTE"],"quote_age_ms":10000,"spread_bps":1.0001000100001711,"estimated_cost_bps":12.500025001251014,"vwap":100000.0,"policy_version":"2026-09-17.1"}
ACTION_ABORTED
```

## Fresh quote

```text
CASE=FRESH_QUOTE_GO INTENDED_SIMULATED_ORDER=BUY BTC-USDT 1000_USDT
EVIDENCE={"mode":"LOCAL_FIXED_REVIEWER_FIXTURE","decision":"GO","reason_codes":["ALL_DECLARED_CHECKS_PASSED"],"quote_age_ms":100,"spread_bps":1.0001000100001711,"estimated_cost_bps":12.500025001251014,"vwap":100000.0,"policy_version":"2026-09-17.1"}
ACTION_ALLOWED_SIMULATION_ONLY
```

This output demonstrates caller control flow against the existing service code
with labeled fixed snapshots. It is not evidence of a live quote, actual
execution, real trading, Alpha, or profitability.
