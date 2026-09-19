# Market Evidence Check

**Can this exact OKX order be executed now under current market liquidity,
cost, and freshness constraints?**

Market Evidence Check is a deterministic pre-execution market-evidence and
feasibility gate for AI agents. Given an instrument, side, and USDT notional,
it evaluates public OKX metadata and displayed order-book depth, then returns a
structured `GO`, `WATCH`, or `REJECT` result.

It is not a trading strategy, price predictor, Alpha generator, or autonomous
trading bot. It has no account, private API, wallet, payment, or order
capability.

## What it measures

- lot-aligned executable quantity;
- snapshot VWAP and estimated one-way cost;
- spread and displayed-depth coverage;
- quote freshness;
- versioned policy checks and structured reason codes.

`GO` means only that the declared checks passed. It is not a recommendation,
profitability claim, fill guarantee, or authorization to trade.

## OKX AI / A2MCP integration

Alpha Factory Agent `#13778`, service **Market Evidence Check**, completed a
real free OKX AI/A2MCP invocation. The official flow reached
`endpoint_result / ready / free_result` and returned HTTP 200 with decision,
reason codes, VWAP, estimated cost, spread, quote age, policy version, and
`OKX_PUBLIC_REST` provenance.

- [OKX AI Agent #13778](https://www.okx.ai/agents/13778)
- [Platform acceptance evidence](evidence/PLATFORM_INVOCATION.md)

## Demo

- [2-minute submission demo](demo/market-evidence-check-demo.webm)
- [Isolated consumer source](demo/demo_consumer.py)
- [Saved deterministic demo output](evidence/DEMO_OUTPUT.md)

The local demo uses labeled fixed snapshots and the existing service engine:

```text
stale quote -> REJECT / STALE_QUOTE -> ACTION_ABORTED
fresh quote -> GO -> ACTION_ALLOWED_SIMULATION_ONLY
```

This is simulation only. No account, API key, order, wallet, or production
trading system is used.

## Reproduce locally

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q test_evidence_api.py
python3 demo/demo_consumer.py
```

The accepted production-state targeted suite passed `17` tests before the
evidence freeze.

## Build-period evidence

- `8b6d43b` — deterministic market-evidence API.
- `0e6f887` — public HTTPS acceptance evidence.
- `1adc6c3` — structured A2MCP missing-input compatibility.
- `67becfa` — real platform acceptance evidence.
- `cd31ab7` — reviewer evidence freeze.

See [the reviewer evidence pack](evidence/REVIEWER_EVIDENCE_PACK.md) for the
verified delta, safe claims, limitations, and explicit do-not-claim list.

## Limitations

- VWAP is a public snapshot estimate, not a guaranteed fill.
- Default fees and slippage buffers are assumptions, not account-observed
  values.
- No historical replay, fault injection, payment/x402, or caller-defined cost
  limit is implemented.
- No real order was submitted or executed.
