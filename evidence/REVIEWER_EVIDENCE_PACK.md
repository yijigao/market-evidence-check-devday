# Market Evidence Check — Reviewer Evidence Pack

## Current status

**PASS: the listed Alpha Factory #13778 service completed a real OKX AI / A2MCP invocation.**

The official flow discovered `Market Evidence Check`, collected its three
required inputs, obtained explicit confirmation for the free call, invoked the
public endpoint, and returned `endpoint_result / ready / free_result` with HTTP
200. The result contained a real public-OKX evidence report with decision,
reason codes, VWAP, estimated cost, spread, quote age, policy version, and data
source. This was not a direct-curl substitute.

Historical blocked attempts are diagnostic history, not the current state.
The transport issue and initial missing-parameter incompatibility were fixed
before the successful platform invocation recorded at
`2026-09-18T14:09:31Z`.

## Reviewer story

**Question:** Can this exact OKX order size be executed now within current
market liquidity, cost, and freshness constraints?

An agent supplies an instrument, side, and USDT notional. Market Evidence
Check reads only public OKX instrument metadata and displayed order-book depth,
converts the requested notional to a valid lot or contract quantity, estimates
snapshot VWAP and one-way execution cost, and checks quote freshness, spread,
depth, and cost against a versioned deterministic policy. It returns
`GO`, `WATCH`, or `REJECT` with reason codes and evidence.

`GO` means only that the declared checks passed. It is not Alpha, a direction
recommendation, a profit promise, or permission to trade. The service has no
account, private API, wallet, payment, or order capability.

## Verified build-period delta

| Feature | Commit | Date | Demo evidence | User value |
|---|---|---|---|---|
| Deterministic public evidence API | `8b6d43b` | 2026-09-17 20:27:13 +08:00 | `evidence_api.py`, focused tests | Converts a proposed order size into an auditable feasibility result. |
| Lot-aware quantity and snapshot VWAP/cost response | `8b6d43b` | 2026-09-17 20:27:13 +08:00 | API tests and sanitized live response | Prevents a caller from treating top-of-book visuals as executable size. |
| Versioned decisions, reasons, provenance, and assumptions | `8b6d43b` | 2026-09-17 20:27:13 +08:00 | Policy `2026-09-17.1`; response fixture | Makes pass/fail behavior inspectable and fail-closed. |
| Public HTTPS business acceptance | `0e6f887` | 2026-09-17 20:30:54 +08:00 | `validation/devday-api-20260917/` | Makes the capability callable outside the development host. |
| A2MCP missing-input compatibility | `1adc6c3` | 2026-09-19 18:01:17 +08:00 | Five focused regressions; platform parameter collection | Lets OKX AI discover and collect the actual required fields. |
| Real OKX AI/A2MCP invocation | `67becfa` | 2026-09-19 18:01:44 +08:00 | `validation/devday-api-20260918/PLATFORM_INVOCATION.md` | Proves the marketplace-to-endpoint user flow, not merely local HTTP success. |

The pre-build research collector and calculation assets are explicitly marked
as pre-existing. Deployment or listing alone is not claimed as the product
delta.

## Caller-side demo evidence

Run from the repository root:

```bash
python3 research/okx_event_probe/submission/reviewer_evidence/demo_consumer.py
```

The script binds only to a random localhost port and calls the existing HTTP
handler and deterministic evidence engine with labeled fixed snapshots:

1. A 10-second-old quote returns `REJECT / STALE_QUOTE`; the consumer prints
   `ACTION_ABORTED`.
2. A 100-ms-old quote passes the declared checks; the consumer prints
   `ACTION_ALLOWED_SIMULATION_ONLY`.

This is a deterministic local consumer-flow demonstration. It is not live
market evidence, historical replay, fault injection, an order simulation, or
a real trade.

## 60–90 second demo script

1. **Problem — 10 seconds.** “A trading agent can see a price, but that does
   not prove its exact order size is executable within acceptable liquidity,
   cost, and freshness constraints.”
2. **Intent — 10 seconds.** Show a proposed, simulation-only request:
   `BTC-USDT`, `buy`, `1000 USDT`. State clearly that no order API exists.
3. **Reject path — 20 seconds.** Run the stale fixed-snapshot case. Point to
   quote age, the 500-ms policy threshold, `STALE_QUOTE`, and
   `ACTION_ABORTED`.
4. **Pass path — 20 seconds.** Run the fresh fixed-snapshot case. Point to the
   displayed VWAP, estimated cost, spread, quote age, policy version, and
   `ACTION_ALLOWED_SIMULATION_ONLY`.
5. **Platform evidence — 15 seconds.** Show the preserved OKX AI/A2MCP
   acceptance summary: Alpha Factory #13778, free service invocation, HTTP
   200, `free_result`, and real `OKX_PUBLIC_REST` evidence fields.
6. **Value — 10 seconds.** “The service gives downstream agents a
   deterministic pre-execution gate. It can stop a simulated action when the
   evidence fails, without predicting price or holding trading authority.”

## Evidence gaps

- Exact listing and registration times are not preserved as committed evidence
  and remain `UNKNOWN`.
- The caller-side demo is deterministic and local; it does not prove real
  fills, market impact, or trading outcomes.
- No historical-replay endpoint or packaged fault-injection mode exists.
- No payment flow or caller-defined `max_cost_bps` exists.

## Safe to claim

- A build-period deterministic market-evidence HTTP API exists.
- It uses public OKX metadata and displayed order-book depth.
- It estimates lot-aligned quantity, snapshot VWAP, spread, quote age, depth,
  and declared one-way costs.
- Missing or invalid evidence fails closed.
- Alpha Factory #13778 completed a real free OKX AI/A2MCP invocation and
  returned a structured business result.
- A local, labeled fixed-snapshot consumer demo proves that `REJECT` aborts a
  downstream simulated action and `GO` permits only a simulated next step.

## Do not claim

- Historical replay is implemented.
- Fault injection is implemented.
- Payment, x402, subscriptions, or monetization are implemented.
- `max_cost_bps` or caller-defined policy thresholds are implemented.
- Any real order was submitted or executed.
- `GO` predicts Alpha, profitability, safety, or fill certainty.
- Account-observed fees or private account data are used.
- Marketplace `Total Sold` represents independent paying users or revenue.
- A listing or registration timestamp that lacks preserved evidence.
- The local reviewer fixture is live market data.

## Submission readiness

**PASS for reviewer narrative and evidence-chain preparation.**

This pack does not authorize production, schema, listing, payment, or product
changes. The existing service freeze remains in force.
