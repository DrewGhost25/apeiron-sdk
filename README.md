# Apeiron SDK

> **The Business Layer for the Agentic Web.**

Apeiron is the most complete open-source implementation of the x402 protocol. It enables API providers, publishers, and AI labs to monetize digital resources with on-chain licensing and automated accounting on the Base blockchain.

[![npm version](https://img.shields.io/npm/v/apeiron-sdk)](https://www.npmjs.com/package/apeiron-sdk)
[![PyPI version](https://img.shields.io/pypi/v/apeiron-sdk)](https://pypi.org/project/apeiron-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Base](https://img.shields.io/badge/Base-Mainnet-0052FF)](https://basescan.org/address/0x6De5e0273428B14d88a690b200870f17888b0d77)

---

## Why Apeiron?

Existing x402 implementations are just "pipes". Apeiron is the financial infrastructure:

**Smart Differential Pricing**
Automatically detect if the requester is a human or an AI agent. Serve a $0.01 "read-only" view to humans and a $1.00 "data-mining" license to bots — with a single line of code.

**On-Chain Licensing**
Every payment generates a cryptographic receipt (`DATA_MINING_LICENSED`) stored permanently on Base blockchain. Protect your IP and give AI agents legal safe-harbor from copyright claims.

**Fair Tiered Fee Structure**
10% fee for micro-payments under $10 USDC, 5% up to $100, 2% above. Fully configurable on-chain — no surprises, fully transparent, visible by anyone.

**Flexible Publisher Pricing**
Every API provider sets their own prices independently. A blogger charges $0.01/read, a financial data provider charges $50.00/AI license. Change anytime with a single transaction — no redeployment needed.

**CFO-Ready Accounting** *(Dashboard — coming soon)*
Stop worrying about USDC bookkeeping. Our upcoming dashboard generates VAT-compliant PDF/XML reports with historical EUR/USD conversions — ready for your accountant.

**Built for the Agentic Stack**
Native support for LangChain, CrewAI, Replit, Lovable, and Vibe Code. Monetize your AI-generated apps in seconds with the `AgentWallet` client.

---

## Quick Start

### Node.js

```bash
npm install apeiron-sdk
```

**Protect your API (Express.js)**

Turn your endpoint into a revenue stream by wrapping your handler with `withX402`:

```javascript
const { withX402 } = require('apeiron-sdk');

// This endpoint now charges $0.01 USDC for humans and $1.00 USDC for AI agents
app.get('/api/premium-data', withX402(
  async (req, res) => {
    // If you reach here, payment is verified on-chain.
    res.json({
      message: "This content is legally licensed.",
      wallet:  req.x402.wallet,
    });
  },
  {
    contentUrl: 'https://yourapi.com/api/premium-data',
  }
));
```

**Environment variables**

```bash
X402_GATEWAY_ADDRESS=0x6De5e0273428B14d88a690b200870f17888b0d77
X402_USDC_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
X402_RPC_URL=https://mainnet.base.org
X402_CONTENT_URL=https://yourapi.com/api/premium-data
```

---

### Python

```bash
pip install apeiron-sdk
```

**Protect your API (Flask)**

```python
from apeiron_sdk import with_x402

@app.route('/api/premium-data')
@with_x402(content_url='https://yourapi.com/api/premium-data')
def get_data():
    x402 = request.environ['x402']
    return jsonify({
        "message": "This content is legally licensed.",
        "wallet":  x402['wallet'],
    })
```

---

## The Agent-to-Agent Economy

Apeiron allows agents to become independent economic actors. Use `AgentWallet` to let your bot automatically pay for its own dependencies — no human intervention required.

**Node.js**

```javascript
const { AgentWallet } = require('apeiron-sdk');

const agent = new AgentWallet({ privateKey: process.env.AGENT_KEY });

// Automatically detects 402, pays USDC on Base, retries with proof of payment.
const data = await agent.fetch('https://api.provider.com/premium-data');
console.log(data);
```

**Python**

```python
from apeiron_sdk import AgentWallet

agent = AgentWallet()  # reads AGENT_KEY from .env

data = agent.fetch('https://api.provider.com/premium-data')
print(data)
```

---

## Register Your Content

Before accepting payments, register your endpoint on the smart contract. You only need to do this once per URL.

```javascript
const { ethers } = require('ethers');

const GATEWAY_ABI = [
  "function registerContent(bytes32 contentId, uint256 humanPrice, uint256 agentPrice, string calldata contentURI) external",
  "function updatePrice(bytes32 contentId, uint256 newHumanPrice, uint256 newAgentPrice) external",
  "function getFeeForAmount(uint256 amount) external view returns (uint256 fee, uint256 publisherReceives)"
];

const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
const signer   = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const gateway  = new ethers.Contract('0x6De5e0273428B14d88a690b200870f17888b0d77', GATEWAY_ABI, signer);

// Compute contentId from your URL
const contentId = ethers.keccak256(ethers.toUtf8Bytes('https://yourapi.com/api/premium-data'));

// Register — every publisher sets their own prices independently
await gateway.registerContent(
  contentId,
  10000,       // $0.01 USDC for human readers  (6 decimals)
  1000000,     // $1.00 USDC for AI agents       (6 decimals)
  'https://yourapi.com/api/premium-data'
);

// Update prices anytime — no redeployment needed
// Emits PriceChanged event on-chain for full audit history
await gateway.updatePrice(contentId, 20000, 2000000);

// Check fee breakdown before registering
const [fee, publisherReceives] = await gateway.getFeeForAmount(1000000);
// fee = 100000 (0.10 USDC), publisherReceives = 900000 (0.90 USDC)
```

---

## Pricing Reference

USDC uses 6 decimals:

| Amount | Units | Typical use |
|--------|-------|-------------|
| $0.01 USDC | 10,000 | Human article read |
| $0.10 USDC | 100,000 | Human premium content |
| $1.00 USDC | 1,000,000 | AI agent license (small) |
| $50.00 USDC | 50,000,000 | AI agent license (dataset) |

---

## Fee Structure

Apeiron uses a tiered fee model — fairer for small publishers, competitive for enterprise:

| Transaction size | Platform fee | Publisher receives |
|-----------------|-------------|-------------------|
| Up to $10 USDC | 10% | 90% |
| $10 — $100 USDC | 5% | 95% |
| Above $100 USDC | 2% | 98% |

Fee parameters are configurable on-chain by the platform owner and fully visible to anyone. No hidden costs. No surprises.

---

## Access Types

| Type | Value | Who | Duration |
|------|-------|-----|----------|
| `READ_ONLY` | 0 | Human readers | Permanent (default) or custom TTL |
| `DATA_MINING_LICENSED` | 1 | AI agents / crawlers | Configurable (e.g. 30 days) |

AI agents receive a permanent on-chain receipt — cryptographic proof of legal license that protects them from copyright claims.

---

## Smart Contract

Deployed on **Base Mainnet** (chainId: 8453):

| Contract | Address |
|----------|---------|
| X402Gateway Proxy | [`0x6De5e0273428B14d88a690b200870f17888b0d77`](https://basescan.org/address/0x6De5e0273428B14d88a690b200870f17888b0d77) |
| X402Gateway Implementation | `0x6137D183058F1bcfC2093Bd3E2E673DDb08f8982` |
| USDC (Base Mainnet) | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

> The Proxy address is permanent and will never change. The implementation can be upgraded by the platform owner to add features — all upgrades are visible on-chain.

[View on BaseScan](https://basescan.org/address/0x6De5e0273428B14d88a690b200870f17888b0d77)

---

## Run the Demo

```bash
git clone https://github.com/DrewGhost25/apeiron-sdk
cd apeiron-sdk/sdk-node
cp .env.example .env
# Add your keys to .env

# Terminal 1 — start the protected API server
node example-server.js

# Terminal 2 — run the AI agent (pays automatically)
node example-agent.js
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Your API / Content                   │
│                                                       │
│   withX402(handler)  /  @with_x402 decorator         │
│                    │                                  │
│                    ▼                                  │
│   ┌──────────────────────────────────────────┐       │
│   │           Apeiron Middleware              │       │
│   │                                          │       │
│   │  1. Detect requester (human vs AI bot)   │       │
│   │  2. No wallet → respond 402              │       │
│   │  3. Wallet present → verify on-chain     │       │
│   │  4. Verified → serve content             │       │
│   └──────────────────────────────────────────┘       │
│                    │                                  │
│                    ▼                                  │
│         Base Blockchain · USDC · x402                │
└──────────────────────────────────────────────────────┘

AgentWallet flow:
  GET /api/data  →  402 Payment Required
       ↓
  Read contentId + price from 402 response
       ↓
  USDC.approve() + gateway.unlockAsAgent()
       ↓
  GET /api/data  (with wallet header)  →  200 OK
```

---

## Roadmap

- [x] Node.js SDK — `withX402` middleware + `AgentWallet` client
- [x] Python SDK — `@with_x402` decorator + `AgentWallet` class
- [x] Smart Contract V2 — upgradeable proxy, tiered fees, full price history on-chain
- [ ] Publisher Dashboard — analytics, bot intelligence, fiscal reports
- [ ] AI Agent Leaderboard — cross-market activity rankings
- [ ] AI model aggregator — one USDC balance for OpenAI, Anthropic, Groq
- [ ] WordPress plugin
- [ ] Replit / Lovable native connector

---

## Contributing

PRs welcome. Open an issue first to discuss what you'd like to change.

---

## License

MIT © Apeiron Protocol
