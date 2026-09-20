# OKX Dev Day — Submission Evidence

## Frozen competition state

- Production source commit: `1878b9c7dc08cfb1b61b1b4724a591a48aa6f2cb`
- Production source SHA-256: `48c51ad0f03bc6b1a426e0e5d96da04703901d8904fbda132815b259a79541ec`
- Agent: Alpha Factory `#13778`
- Service: Market Evidence Check
- Marketplace service ID: `40781`
- Platform service UUID: `257729dc-8464-4323-b624-73afd7339e35`
- Policy version: `2026-09-17.1`
- Public endpoint: `POST https://devday.167-179-82-72.nip.io/v1/evidence/check`
- Listing status checked on 2026-09-20: `approvalStatus=3`, Listed

This is the feature-freeze boundary. Later documentation must not be presented
as a product capability change.

## Product in one sentence

Market Evidence Check is a deterministic pre-execution gate that tells an AI
agent whether a specific OKX order size passes declared liquidity, freshness,
and estimated-cost constraints before any simulated action proceeds.

## Problem

A visible market price does not establish that an exact order size is
executable at an acceptable cost or that the quote is fresh. An AI caller needs
an inspectable, fail-closed answer before it considers proceeding.

## Solution

The caller supplies an OKX instrument, side, USDT notional, and an explicit
maximum estimated cost. The service reads public OKX metadata and displayed
depth, converts the notional to a valid lot-aligned quantity, calculates
snapshot VWAP and estimated one-way cost, checks spread and quote freshness,
and returns `GO`, `WATCH`, or `REJECT` with structured reason codes.

`GO` means only that the declared checks passed. It is not a prediction,
profitability claim, fill guarantee, or authorization to trade.

## Short end-to-end demo

Question:

> Can this BTC-USDT-SWAP 1,000 USDT buy order be executed now within a
> 1 bps cost limit?

Flow:

```text
OKX AI
  -> Alpha Factory #13778
  -> A2MCP collects instrument, side, notional_usdt, max_cost_bps
  -> Market Evidence Check reads OKX public market data
  -> REJECT / ESTIMATED_COST_EXCEEDS_POLICY
  -> estimated cost ~= 12 bps, caller limit = 1 bps
```

Change only the caller's limit to `max_cost_bps=100`:

```text
same instrument / side / notional
  -> GO / ALL_DECLARED_CHECKS_PASSED
  -> estimated cost ~= 12 bps, caller limit = 100 bps
```

The two calls used separate live snapshots, so market values are not claimed
to be byte-identical. They were materially consistent; the decisive policy
change was the caller's cost constraint.

## Verified A2MCP evidence

Both calls used fresh official service discovery, a new A2MCP invocation
generation, structured four-field parameter collection, explicit free-call
confirmation, and the official `free_result` flow. Neither result was produced
by direct curl.

| Field | 1 bps call | 100 bps call |
|---|---:|---:|
| Checked at (UTC) | `2026-09-20T04:35:25.530818Z` | `2026-09-20T04:36:41.726270Z` |
| HTTP/platform result | `200 / free_result` | `200 / free_result` |
| Decision | `REJECT` | `GO` |
| Reason | `ESTIMATED_COST_EXCEEDS_POLICY` | `ALL_DECLARED_CHECKS_PASSED` |
| Estimated one-way cost | `12.006218 bps` | `12.006217 bps` |
| Cost threshold | `1 bps` | `100 bps` |
| Snapshot VWAP | `80409.6` | `80421.6` |
| Spread | `0.012436 bps` | `0.012434 bps` |
| Quote age | `9 ms` | `12 ms` |
| Depth complete | `true` | `true` |
| Evidence hash | `sha256:1170e00dec6b110383062d19154f9a7294485f4e5999c4617aa1f9e0b058c4c2` | `sha256:6c7688d5ac2d0757ce8b7a672ff85777350154135b8e5e745a67df05959f3334` |

The displayed depth, VWAP, spread, freshness, lot conversion, and cost
calculation continued to use the same engine and policy. `max_cost_bps` changed
only the estimated-cost threshold for that request. A direct API request that
omits the field remains backward-compatible and uses the 30 bps default.

## Why OKX AI / A2MCP matters

The integration turns a public market-data calculation into a callable agent
decision gate. OKX AI discovers the listed service, gathers typed parameters,
routes them through A2MCP, requests explicit confirmation, and returns the
structured evidence result to the caller. This demonstrates a real platform
workflow rather than a standalone API demo.

## Technical architecture

```text
OKX public instrument metadata + 400-level order book
  -> deterministic lot/contract conversion
  -> depth-aware snapshot VWAP and estimated cost
  -> versioned freshness/spread/depth/cost checks
  -> HTTPS evidence API
  -> OKX AI / A2MCP
  -> GO / WATCH / REJECT + reason codes + provenance
```

## User value

- Converts a proposed order size into a concrete, auditable feasibility check.
- Lets the caller state its own estimated-cost constraint.
- Distinguishes executable evidence from a visually attractive top-of-book
  price.
- Fails closed on stale, incomplete, unsupported, or unavailable evidence.
- Gives downstream agents structured reasons to stop a simulated action.

## Safety boundary

- Public OKX market data only.
- No trading API key, account access, custody, wallet, payment, or order route.
- No automatic execution or real fills.
- No price-direction prediction, Alpha, or profitability guarantee.
- VWAP is a public snapshot estimate, not a guaranteed execution price.
- Fee and slippage inputs are assumptions unless independently supplied.

## Demo steps

1. Open Alpha Factory `#13778` and select Market Evidence Check.
2. Ask the 1 bps question above.
3. Show all four collected parameters.
4. Confirm the free invocation.
5. Highlight `REJECT`, the reason code, approximately 12 bps estimated cost,
   VWAP, spread, and quote age.
6. Start a fresh invocation with the same market inputs and a 100 bps limit.
7. Highlight `GO` and the same evidence categories.
8. State that this is a pre-execution evidence gate and cannot trade.

## Current limitations

- Live snapshots naturally change between calls; the service does not provide
  atomic multi-request snapshot replay.
- Public displayed depth may differ from an eventual fill.
- Default fee and slippage assumptions are not account-observed values.
- No historical replay, fault injection, payment, trading, or execution is
  implemented.
- No claim is made about demand, user count, revenue, or profitability.

## Next commercial experiment

Keep the service free and measure whether independent callers repeatedly use
their own cost limits in real pre-execution checks. Only verified repeated use
and explicit willingness-to-pay feedback would justify a later pricing
experiment; neither is claimed today.

## Supporting evidence

- [Original OKX AI platform acceptance](../../validation/devday-api-20260918/PLATFORM_INVOCATION.md)
- [Public HTTPS acceptance](../../validation/devday-api-20260917/ACCEPTANCE.md)
- [Reviewer evidence index](SUBMISSION_EVIDENCE_INDEX.md)
- [Reviewer evidence pack](REVIEWER_EVIDENCE_PACK.md)

No token, cookie, wallet secret, account identifier, confirmation ID, routing
payload, or private credential is included in this document.
