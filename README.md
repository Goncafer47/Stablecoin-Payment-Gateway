# Stablecoin-Payment-Gateway
Self-hosted, non-custodial stablecoin payment gateway with x402 and invoice checkout. Accepts USDC, USDT, PYUSD and DAI across 8 networks with QR payments, payment links, settlement tracking and signed webhooks. REST API, micropayments, exports, zero platform fees and no KYC. Python, cross-platform.
---

<div align="center">

# Stablecoin Payment Gateway

**Self-Hosted x402 Gateway — Multi-Chain USDC/USDT Merchant API**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge)]()
[![x402](https://img.shields.io/badge/Protocol-x402%20%7C%20HTTP%20402-FF6600?style=for-the-badge)]()
[![Custody](https://img.shields.io/badge/Custody-Non--Custodial-brightgreen?style=for-the-badge)]()

---

*Self-hosted stablecoin payment gateway with x402 protocol support.<br>Accept USDC/USDT across 8 chains with invoices, payment links, signed webhooks<br>and HTTP 402 pay-per-request monetization — funds settle straight to your wallet.*

[Features](#features) · [How x402 Works](#how-x402-works) · [Invoices](#invoices--checkout) · [Getting Started](#getting-started) · [Configuration](#configuration) · [Usage](#usage) · [FAQ](#faq)

</div>

---

## Features

<table>
<tr>
<td width="50%">

### Payments
| Feature | Status |
|---------|--------|
| Fixed-Amount Invoices | ✅ |
| Unique Deposit Address per Invoice | ✅ |
| Shareable Payment Links | ✅ |
| QR Checkout Payloads | ✅ |
| x402 HTTP 402 Paywall | ✅ |
| Under/Over-Payment Handling | ✅ |
| Invoice TTL & Auto-Expiry | ✅ |
| Mempool + Block Watchers | ✅ |

</td>
<td width="50%">

### Merchant Stack
| Feature | Status |
|---------|--------|
| HMAC-SHA256 Signed Webhooks | ✅ |
| Scoped Merchant API Keys | ✅ |
| Key Rotation with Grace Period | ✅ |
| Per-Chain Confirmation Policy | ✅ |
| xpub Address Derivation | ✅ |
| Settlement CSV/JSON Export | ✅ |
| 0% Platform Fees / No KYC | ✅ |
| Self-Hosted (Docker-friendly) | ✅ |

</td>
</tr>
</table>

---

## How x402 Works

x402 is an open payment standard built on HTTP — it resurrects the `402 Payment Required` status code so any endpoint can become payable in one line:

```
Client                          Gateway (resource server)              Facilitator
  │  GET /api/premium                 │                                    │
  │ ────────────────────────────────> │                                    │
  │  402 + accepted networks/assets   │                                    │
  │ <──────────────────────────────── │                                    │
  │  GET + X-PAYMENT (signed payload) │                                    │
  │ ────────────────────────────────> │  POST /verify ──────────────────>  │
  │                                   │ <─────────────────────── valid ─── │
  │                                   │  POST /settle ──────────────────>  │
  │                                   │ <──────────── tx hash (settled) ── │
  │  200 OK + PAYMENT-RESPONSE        │                                    │
  │ <──────────────────────────────── │                                    │
```

1. **402 Challenge** — unpaid requests get a `402` response listing accepted `(network, asset)` pairs
2. **X-PAYMENT** — the client signs a stablecoin transfer authorization and retries
3. **Verify & Settle** — the gateway verifies the payload through the facilitator and settles on-chain
4. **Receipt** — the response carries `PAYMENT-RESPONSE` with the settlement transaction hash

The gateway supports the `exact` scheme (fixed amount per call) on Base, Ethereum, Polygon and Arbitrum, with server-side control over which networks clients may pay on.

---

## Invoices & Checkout

Classic merchant flow for shops, SaaS and donations:

- **Invoice** — fixed amount in USDC/USDT, unique deposit address derived from your xpub, 30-minute TTL (configurable)
- **Checkout URL** — hosted page with QR payload; works from any wallet app
- **Watchers** — mempool scanner detects the payment in seconds; block watcher counts confirmations to the per-chain floor
- **Webhooks** — `invoice.created → invoice.paid → invoice.settled`, signed with HMAC-SHA256, retried with `5s → 30s → 120s` backoff
- **Edge cases** — underpayments within tolerance auto-accept; overpayments credit the customer balance; expired invoices release the address back to the pool

### Why self-hosted?

| | Hosted processors | **This gateway** |
|---|:---:|:---:|
| Platform fee | 0.5–1% | **0%** |
| Custody | Processor holds funds | **Your wallet, your keys** |
| KYC | Required | **None** |
| Networks | Their choice | **You decide** |
| Stack | Closed SaaS | **Open source, audit everything** |

---

## Getting Started

### Prerequisites

- **Python** 3.10 or higher
- **pip** (latest recommended)
- An EVM wallet address (or xpub) to receive payouts
- Optional: your own x402 facilitator for production mainnet settlement

### Installation

**Windows:**

```bash
git clone https://github.com/Goncafer47/Stablecoin-Payment-Gateway.git
cd Stablecoin-Payment-Gateway
run.bat
```

**Linux / macOS:**

```bash
git clone https://github.com/Goncafer47/Stablecoin-Payment-Gateway.git
cd Stablecoin-Payment-Gateway
chmod +x run.sh
./run.sh
```

**Manual:**

```bash
pip install -r requirements.txt
python main.py
```

### Dependency Table

| Package | Version | Purpose |
|---------|---------|---------|
| rich | ≥13.7.0 | Terminal UI, tables, progress bars |
| cryptography | ≥43.0.1 | Webhook signing & key handling |
| requests | ≥2.32.3 | Facilitator & RPC calls |
| aiohttp | ≥3.10.11 | Async chain watchers |
| qrcode | ≥8.0 | Checkout QR payloads |
| web3 | ≥7.0.0 | On-chain settlement verification |

---

## Configuration

Full `config.json` example:

```json
{
    "merchant": {
        "name": "Demo Store",
        "pay_to_address": "0xYourWalletAddress",
        "xpub": "",
        "callback_url": "https://merchant.example.com/hooks/invoices"
    },
    "invoice": {
        "ttl_minutes": 30,
        "underpayment_tolerance_pct": 0.5,
        "overpayment_action": "credit",
        "confirmations": {"ethereum": 12, "base": 12, "polygon": 64, "tron": 19}
    },
    "chains": {
        "base": {"enabled": true, "rpc": "https://mainnet.base.org"},
        "ethereum": {"enabled": true, "rpc": "https://eth.llamarpc.com"},
        "tron": {"enabled": true, "rpc": "https://api.trongrid.io"}
    },
    "tokens": {
        "USDC": {"enabled": true, "decimals": 6},
        "USDT": {"enabled": true, "decimals": 6}
    },
    "x402": {
        "enabled": true,
        "facilitator_url": "https://x402.org/facilitator",
        "scheme": "exact",
        "paywall_routes": ["/api/premium", "/api/download"]
    },
    "webhooks": {
        "enabled": true,
        "retry_backoff_sec": [5, 30, 120],
        "signing_header": "X-Signature-256"
    }
}
```

---

## Usage

```
╔══════════════════════════════════════════════════════════════════════╗
║              STABLECOIN PAYMENT GATEWAY v2.6.0                   ║
║         Self-Hosted x402 Stablecoin Payment Gateway                  ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ── Sales ───────────────────────────────────────────────────────    ║
║  │ [1]  🧾 Create Invoice      Fixed-amount charge + address       ║ ║
║  │ [2]  🔗 Payment Links       Shareable checkout URLs             ║ ║
║                                                                      ║
║  ── Integration ─────────────────────────────────────────────────    ║
║  │ [3]  📬 Webhooks            HMAC-signed notifications           ║ ║
║  │ [4]  🧱 x402 Paywall        HTTP 402 pay-per-request routes     ║ ║
║                                                                      ║
║  ── Operations ──────────────────────────────────────────────────    ║
║  │ [5]  💸 Settlement Monitor  Confirmations & payout status       ║ ║
║  │ [6]  🔑 Merchant API Keys   Issue & rotate REST credentials     ║ ║
║  │ [7]  ⛓️  Chains & Tokens    USDC/USDT across 8 networks         ║ ║
║  │ [8]  ⚙️  Settings           Server, TTL, preferences            ║ ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Watchers: ● 6 chains live  │  Open invoices: 14  │  24h: $8,412.55 ║
╚══════════════════════════════════════════════════════════════════════╝

Select option [#]: 1
```

### Terminal Output — Invoice Creation

```
[10:14:52] Deriving deposit address... xpub path m/44'/60'/0'/1042
[10:14:52] Invoice inv_3f9a2c81d4e5b607 registered (live mode)
[10:14:53] ┌─────────────────────────────────────────────────────┐
[10:14:53] │  Amount          249.00 USDC                        │
[10:14:53] │  Chain           Base                               │
[10:14:53] │  Deposit To      0x4b21...9F02                      │
[10:14:53] │  Confirmations   0/12                               │
[10:14:53] │  Expires         30 minutes                         │
[10:14:53] │  Checkout        https://pay.example.com/i/inv_3f9a │
[10:14:53] └─────────────────────────────────────────────────────┘
[10:15:41] Mempool hit: 249.00 USDC from 0x88c1...A2d4
[10:16:07] Confirmations 12/12 → invoice.settled
[10:16:07] Webhook invoice.settled → 200 OK (138 ms)
```

---

## Project Structure

```
Stablecoin-Payment-Gateway/
├── main.py                 # Entry point and menu system
├── config.py               # Configuration loader (JSON + defaults)
├── bot_actions.py          # Invoicing, webhooks, settlement handlers
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows launcher
├── run.sh                  # Linux/macOS launcher
├── about.txt               # Project description (SEO)
├── tags.txt                # Repository tags / SEO keywords
├── .gitignore              # Git ignore rules
├── actions/
│   ├── __init__.py
│   ├── about.py            # About panel display
│   ├── install.py          # Dependency installer
│   └── settings.py         # Settings display and setup
├── pipeline/
│   ├── __init__.py         # Environment bootstrap & decorator
│   ├── environ.py            # Environment configuration & credentials
│   ├── session.py        # HTTP client for service communication
│   ├── sealing.py          # Data encoding and validation utilities
│   ├── materializer.py         # Data processing pipeline
│   ├── records.py          # Diagnostics shim
│   └── ui.py               # Rich console UI components
└── release/
    └── README.md           # Pre-compiled release info
```

---

## FAQ

<details>
<summary><b>Is the gateway really non-custodial?</b></summary>
<br>
Yes. Deposit addresses are derived from your extended public key (xpub) or map directly to your payout address. Private keys never touch the gateway — payments settle on-chain directly into your wallet. There is no intermediate balance, no withdrawal step and no platform fee.
</details>

<details>
<summary><b>What is x402 and why should I care?</b></summary>
<br>
x402 is an open standard for internet-native payments built on the HTTP <code>402 Payment Required</code> status code. It lets you charge per API request — one line on the server, one function on the client — with stablecoin settlement. It is the emerging standard for machine-to-machine and AI-agent payments, alongside classic checkout flows.
</details>

<details>
<summary><b>Which facilitator should I use?</b></summary>
<br>
For testnets and evaluation, the public x402.org facilitator works out of the box. For production mainnet traffic, run your own facilitator or use a production facilitator provider — the public endpoint is a convenience, not a production path. Set <code>x402.facilitator_url</code> accordingly.
</details>

<details>
<summary><b>How are webhooks secured?</b></summary>
<br>
Every webhook payload is signed with HMAC-SHA256 using your <code>webhooks.secret</code> and delivered with the signature in the <code>X-Signature-256</code> header. Failed deliveries retry with exponential backoff (5s → 30s → 120s). Always verify the signature server-side before acting on an event.
</details>

<details>
<summary><b>Which chains and tokens are supported?</b></summary>
<br>
USDC and USDT on Ethereum, Base, BNB Chain, Polygon, Arbitrum and Tron are enabled by default; Solana and TON can be toggled on, and PYUSD/DAI are one config flag away. Each chain has its own confirmation floor (e.g. 12 blocks on Base, 64 on Polygon, 19 on Tron).
</details>

<details>
<summary><b>Can I run it in Docker?</b></summary>
<br>
Yes — the gateway is a single Python process with no external database requirement, so a minimal <code>python:3.11-slim</code> image is enough. No full node needed: watchers use public or your own RPC endpoints.
</details>

---

<div align="center">

## Disclaimer

**This software is provided for educational and research purposes only.** Running a payment gateway may be a regulated activity in your jurisdiction — you are solely responsible for compliance with applicable laws (including AML/KYC obligations that may apply to merchants). The authors assume no liability for any consequences arising from the use of this tool.

---

**Donations** — If this tool has been useful, consider supporting development:

`0x4Bb3c7dB378447F2d9af791D4B7B3E4B3Df53b48`

---

*Your store, your keys, your settlement — no middlemen.*

</div>
