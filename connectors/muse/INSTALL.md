# Install Market Evidence Check on Muse

This is a free, read-only custom connector. It checks a stated OKX order size against a current public order-book snapshot. It does not place orders and needs no API key or account.

1. Open Muse.
2. Paste the prompt in the **“Paste this into Muse”** section of the connector brief:
   https://raw.githubusercontent.com/yijigao/market-evidence-check-devday/main/connectors/muse/muse.md
3. Let Muse read the brief and OpenAPI specification, build the connector, and run the three smoke tests.
4. Review the reported decision, estimated snapshot cost, quote age, depth completeness, and evidence hash.

If Muse asks for an exchange API key, wallet, password, or seed phrase, stop. This connector requires none of those.

`GO` only means the current public snapshot passed the declared checks. It is not a trading recommendation or a fill guarantee.
