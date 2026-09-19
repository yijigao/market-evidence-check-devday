# OKX AI platform invocation acceptance

- Time: `2026-09-18T12:53:59Z` (UTC)
- Result: `BLOCKED`
- Failed layer: `routing`
- Official client: Onchain OS CLI `4.6.0`

## Fresh platform discovery

- Public agent search returned `Alpha Factory`, Agent `#13778`.
- The current marketplace service list returned `Market Evidence Check` as an
  active `A2MCP` service priced at `0 USDT`.
- The current registered endpoint was the expected public evidence-check URL.
- Agent approval state was `Listed — eligible for task recommendations`.

## Routing result

The official precise service search rejected routing because the active
account has no User identity. A read-only `gate-check --role user` independently
confirmed that the wallet login is valid but the User identity gate is absent.
The account currently contains only the ASP identity for Agent `#13778`.

No routing JSON, confirmation ID, or opaque state was manually constructed.
The A2MCP probe and endpoint invocation were not reached, and no direct curl was
used as platform-invocation evidence.

## Required next action

Creating a User identity would be required before this account can perform the
buyer-side OKX AI/A2MCP invocation. That state-changing action was explicitly
outside this acceptance run's authorization.

No token, cookie, wallet secret, email address, complete wallet address, or
internal routing payload is recorded here.

## Final platform acceptance

- Time: `2026-09-18T14:09:31Z` (UTC)
- Result: `PASS`
- Platform result: `endpoint_result / ready / free_result`
- Provider: `Alpha Factory #13778`
- Service: `Market Evidence Check`
- Invocation: free `POST`, HTTP `200`
- Parameters: `BTC-USDT-SWAP`, `buy`, `1000 USDT`
- Business result: `COMPLETE`, decision `GO`, reason
  `ALL_DECLARED_CHECKS_PASSED`
- Evidence summary: VWAP `80120.5`, estimated one-way cost
  `12.006240603991348 bps`, spread `0.012481215772019993 bps`, quote age
  `17 ms`, policy `2026-09-17.1`, source `OKX_PUBLIC_REST`

This acceptance used fresh official service discovery, the A2MCP missing-input
round trip, explicit user confirmation of the free invocation, and the official
`confirm-free` flow. It was not a direct curl acceptance. No confirmation ID,
routing payload, token, cookie, wallet secret, or private credential is stored.

## Authorized follow-up attempt

- A User identity was created through the official Onchain OS flow and then
  independently recognized by `gate-check --role user`.
- Fresh official discovery again selected Agent `#13778`, service
  `Market Evidence Check`, type `A2MCP`, price `0 USDT`.
- `task-create-prepare` returned the expected structured
  `service_routing / a2mcp_service_confirmed` state for that exact service.
- The unmodified current `payload` was passed programmatically to the official
  A2MCP probe through its Base64 transport; no routing JSON or opaque ID was
  manually reconstructed.
- The probe terminated at `endpoint_probe` with reason `endpoint_failure` and
  the readable message `endpoint request failed`.

Result remains `BLOCKED`, now at the `A2MCP probe → endpoint` boundary. No
`input_required`, `free_confirmation_required`, or `free_result` was returned.
No direct curl was used as substitute acceptance evidence, and production was
not changed.
