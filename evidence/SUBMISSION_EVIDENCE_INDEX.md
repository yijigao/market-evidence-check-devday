# Alpha Factory — Dev Day Submission Evidence Index

## Current status

**FROZEN / VERIFIED:** Alpha Factory #13778 completed a real free OKX AI/A2MCP
invocation. The official flow returned `endpoint_result / ready / free_result`
and HTTP 200 with a complete public-market evidence result. Production and the
listed service are frozen.

Start here, then use:

- [Reviewer evidence pack](REVIEWER_EVIDENCE_PACK.md)
- [Isolated consumer](demo_consumer.py)
- [Saved demo output](DEMO_OUTPUT.md)
- Platform acceptance: `../../validation/devday-api-20260918/PLATFORM_INVOCATION.md`
- Public HTTPS acceptance: `../../validation/devday-api-20260917/ACCEPTANCE.md`

## Product one-liner

**Can this exact OKX order be executed now under current market liquidity,
cost, and freshness constraints?**

Market Evidence Check is a pre-execution market-evidence and feasibility gate.
It is not a trading strategy, does not predict price direction, and cannot
execute a real trade.

## Problem

An agent seeing a market price does not know whether its exact intended size is
supported by displayed depth, whether snapshot VWAP and estimated cost remain
reasonable, or whether the quote is fresh enough to use. Acting without those
checks can turn a visually attractive quote into an unrealistic or unsafe
action.

## User flow

1. A caller describes an intended instrument, side, and USDT notional.
2. The service reads public OKX instrument metadata and displayed depth.
3. It calculates lot-aligned quantity, snapshot VWAP, estimated one-way cost,
   spread, depth coverage, and quote freshness.
4. A versioned deterministic policy returns `GO`, `WATCH`, or `REJECT` with
   structured reason codes and assumptions.
5. The downstream caller allows only a simulated next step or aborts. There is
   no order endpoint or trading credential.

## Verified build-period delta

| Commit | Date | Feature | User value | Evidence path |
|---|---|---|---|---|
| `8b6d43bb4cb8f9dc09c6487d0a39bb6b7e9e1877` | 2026-09-17 20:27:13 +08:00 | Deterministic market-evidence API | Turns an intended size into an inspectable feasibility result. | `../../evidence_api.py`, `../../test_evidence_api.py` |
| `0e6f887d9b29e7a51954abcf1607061a589de81e` | 2026-09-17 20:30:54 +08:00 | Public HTTPS acceptance evidence | Proves external delivery without treating deployment alone as product value. | `../../validation/devday-api-20260917/` |
| `1adc6c38474625f92843f75b05ca7e3f0c95b8f1` | 2026-09-19 18:01:17 +08:00 | Structured A2MCP `input_required` compatibility | Lets OKX AI collect the three real required fields and preserve fail-closed validation. | `../../evidence_api.py`, `../../test_evidence_api.py` |
| `67becfab1886d493042d1b8e5ff4560071f22982` | 2026-09-19 18:01:44 +08:00 | Real platform acceptance record | Proves discovery-to-result through OKX AI/A2MCP rather than direct curl. | `../../validation/devday-api-20260918/PLATFORM_INVOCATION.md` |

Pre-build collector and research capabilities are not claimed as competition
delta. Exact listing and registration timestamps are `UNKNOWN`.

## Production implementation

The frozen implementation uses public OKX metadata and order-book depth,
verified lot/contract conversion, snapshot VWAP, explicit fee/slippage
assumptions, a versioned policy, structured reason codes, evidence provenance,
and fail-closed error handling. It contains no private API, account, payment,
wallet, or order capability.

Production implementation commit:
`1adc6c38474625f92843f75b05ca7e3f0c95b8f1`.

## Platform acceptance

At `2026-09-18T14:09:31Z`, the official OKX AI/A2MCP path returned a free
result for Alpha Factory #13778 / Market Evidence Check. The response was
`COMPLETE` and contained decision, reason codes, VWAP, estimated cost, spread,
quote age, policy version, and `OKX_PUBLIC_REST` provenance. No direct curl was
used as platform-acceptance evidence.

Acceptance evidence commit:
`67becfab1886d493042d1b8e5ff4560071f22982`.

## Caller-side demo

The isolated demo runs the existing Handler and deterministic engine on a
random localhost port with labeled fixed snapshots:

- stale quote → `REJECT / STALE_QUOTE` → `ACTION_ABORTED`
- fresh quote → `GO` → `ACTION_ALLOWED_SIMULATION_ONLY`

It is simulation only: no account, API key, order, wallet, production endpoint,
or production trading is used. See `demo_consumer.py` and `DEMO_OUTPUT.md`.

## 60–90 second reviewer narrative

“An agent intends to buy 1,000 USDT of an OKX instrument, but a visible price
does not prove that exact size is feasible. Before any action, it asks Market
Evidence Check. The service converts the notional to a valid lot-aligned
quantity, walks displayed depth for snapshot VWAP, estimates cost, and checks
spread and quote freshness. In the first fixed-snapshot demonstration, the
quote is stale: the service returns `REJECT / STALE_QUOTE`, and the downstream
caller prints `ACTION_ABORTED`. In the second, the declared checks pass and the
caller prints `ACTION_ALLOWED_SIMULATION_ONLY`. The same service has completed
a real free OKX AI/A2MCP invocation. This reduces unrealistic agent actions by
placing deterministic evidence and a fail-closed decision gate before any
possible execution system. It does not predict direction and cannot trade.”

## Safe claims

- Deterministic market-evidence API.
- OKX public market data.
- Lot-aligned executable quantity.
- Snapshot VWAP and estimated execution cost.
- Spread and quote-freshness checks.
- Structured reason codes and fail-closed behavior.
- Real OKX AI/A2MCP free-call acceptance.
- `REJECT` can gate a downstream simulated action.

## Do-not-claim

- Historical replay implemented.
- Fault injection implemented.
- Payment or x402 implemented.
- `max_cost_bps` implemented.
- Real trading or actual execution.
- Profitability, Alpha, fill certainty, or performance guarantees.
- Account-observed fees or private account data.
- Listing or registration timestamps when evidence is unavailable.
- The local fixed-snapshot demo is live market data.

## Known gaps

- Exact listing and registration timestamps are unavailable.
- The local caller demo proves deterministic control flow, not real fills or
  market impact.
- Default fees and slippage buffers are assumptions, not account-observed
  values.
- No historical replay, fault injection, payment, or caller-defined cost limit
  is implemented.

## Commit index

- `8b6d43bb4cb8f9dc09c6487d0a39bb6b7e9e1877` — initial deterministic API.
- `0e6f887d9b29e7a51954abcf1607061a589de81e` — public endpoint acceptance.
- `1adc6c38474625f92843f75b05ca7e3f0c95b8f1` — A2MCP compatibility.
- `67becfab1886d493042d1b8e5ff4560071f22982` — platform acceptance evidence.

All four references were verified in Git. This package adds documentation and
an isolated reviewer demonstration only; it adds no product capability.
