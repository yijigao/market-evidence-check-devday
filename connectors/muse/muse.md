# Market Evidence Check — Muse Custom Connector Brief

Use this brief to connect a free, read-only OKX market-evidence checker to Muse. It uses public market data only. There is no API key, account, wallet, payment, or order capability.

## Paste this into Muse

```text
Build a custom connector for Market Evidence Check and save it as a reusable skill named "market-evidence-check".

Read this brief first:
https://raw.githubusercontent.com/yijigao/market-evidence-check-devday/main/connectors/muse/muse.md

OpenAPI specification:
https://raw.githubusercontent.com/yijigao/market-evidence-check-devday/main/connectors/muse/openapi.json

Rules:
- Authentication: none. Do not ask me for an API key, exchange credential, wallet, password, or seed phrase.
- Only call the API base URL in the OpenAPI specification: https://devday.167-179-82-72.nip.io
- Use GET /__devday_healthz for liveness and POST /v1/evidence/check for a check.
- A request is: instrument, side ("buy" or "sell"), notional_usdt, and optionally max_cost_bps (default 30).
- GO means only that the current public snapshot passed the declared liquidity, cost, spread, freshness, and displayed-depth checks. It is not a buy/sell recommendation, trading signal, profit prediction, fill guarantee, or permission to trade.
- Fail closed: if the API returns WATCH, REJECT, HTTP 400, HTTP 502, invalid JSON, or a timeout, do not convert it into GO and do not suggest placing an order.
- Never place an order, connect a wallet, request exchange credentials, or change the stated cost limit without telling me.

After building it, run these smoke tests and report the results:
1. Health check.
2. Check buying 1000 USDT of BTC-USDT with max_cost_bps 30.
3. Send side "hold" and confirm the API rejects the input.

For every result, show: decision, reason_codes, executable_price_vwap, estimated_one_way_cost_bps, quote age, depth completeness, policy_version, checked_at_utc, and evidence_hash.
```

## Connection details

| Item | Value |
|---|---|
| Product | Market Evidence Check |
| Company / developer | Alpha Factory |
| Website | https://www.amzwatch.xyz/market-evidence-check/ |
| API base URL | `https://devday.167-179-82-72.nip.io` |
| OpenAPI | https://raw.githubusercontent.com/yijigao/market-evidence-check-devday/main/connectors/muse/openapi.json |
| This brief | https://raw.githubusercontent.com/yijigao/market-evidence-check-devday/main/connectors/muse/muse.md |
| API docs | https://www.amzwatch.xyz/market-evidence-check/docs.html |
| Privacy | https://www.amzwatch.xyz/market-evidence-check/privacy.html |
| Terms | https://www.amzwatch.xyz/market-evidence-check/terms.html |
| Support | founder@amzwatch.xyz |
| Authentication | None |
| Content type | `application/json` |
| Allowed API host | `devday.167-179-82-72.nip.io` |

## Tool contract

### `getHealth`

`GET /__devday_healthz`

Expected response: HTTP 200 with `status: "ok"`.

### `checkEvidence`

`POST /v1/evidence/check`

Example request:

```json
{
  "instrument": "BTC-USDT",
  "side": "buy",
  "notional_usdt": 1000,
  "max_cost_bps": 30
}
```

Required fields:

- `instrument`: OKX instrument ID, such as `BTC-USDT`, `ETH-USDT`, or `BTC-USDT-SWAP`.
- `side`: `buy` or `sell`.
- `notional_usdt`: stated USDT amount to test, greater than 0 and no more than 1,000,000. This is a hypothetical check size, not an order.

Optional fields:

- `max_cost_bps`: maximum acceptable estimated one-way cost, from 0 to 1000 bps. Default: 30.
- `cost_assumptions.taker_fee_bps`: caller-supplied fee assumption. Default policy assumption: 10 bps.
- `cost_assumptions.slippage_buffer_bps`: caller-supplied buffer. Default policy assumption: 2 bps.

A complete report includes `decision`, `reason_codes`, `market_evidence`, `execution_cost`, `policy_checks`, `policy_version`, `data_quality.source`, `evidence_hash`, `checked_at_utc`, and `report_status: "COMPLETE"`.

## How to explain a result

- `GO`: the current public snapshot passed all declared checks. Do not call it safe, profitable, recommended, or guaranteed to fill.
- `WATCH`: evidence could not be completed or upstream public data was unavailable. Treat it as no evidence, not approval.
- `REJECT`: the input was invalid or at least one declared check failed. Show the reason codes.

Always separate observed snapshot values from assumptions. The VWAP is a snapshot estimate from displayed depth. The taker fee is a policy or caller assumption, not the user's actual exchange-account fee.

## Safety limits

This connector must never:

- place, modify, or cancel an order;
- access an exchange account or wallet;
- request or store API keys, passwords, seed phrases, or private keys;
- claim that GO predicts price movement, profit, alpha, or an actual fill;
- hide a failed health check, stale quote, incomplete depth, or API error.

## If installation fails

Stop and report the exact step that failed: fetching this brief, fetching the OpenAPI specification, creating the skill, calling the health endpoint, or running a smoke test. Include the HTTP status and error message if available. Do not invent a replacement endpoint or ask for credentials as a workaround.
