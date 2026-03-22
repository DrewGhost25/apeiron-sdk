# Apeiron SDK

> The payment layer for the agentic web. Monetize your API with one line of code — humans pay cents, AI agents pay licenses, automatically.

[![npm version](https://img.shields.io/npm/v/@apeiron/sdk)](https://www.npmjs.com/package/@apeiron/sdk)
[![PyPI version](https://img.shields.io/pypi/v/apeiron-sdk)](https://pypi.org/project/apeiron-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is Apeiron?

Apeiron is an open-source SDK that adds a **payment gateway** to any API endpoint using the [x402 protocol](https://x402.org) and USDC on Base blockchain.

- **For API providers**: wrap your endpoint with `withX402()` — done. You receive USDC instantly for every request.
- **For AI agents**: use `AgentWallet` to automatically pay and access any x402-protected API.
- **No subscriptions. No credit cards. No registration.**

```
Human reader  →  $0.10 USDC  →  Instant access
AI agent      →  $1.00 USDC  →  DATA_MINING_LICENSED (on-chain receipt)
```

---

## How it works

```
1. Agent calls your API
2. Your API responds 402 Payment Required (with payment instructions)
3. Agent reads instructions, pays USDC on Base blockchain
4. Agent retries with wallet address
5. Your API verifies payment on-chain → serves content
```

Everything is verified on the Base blockchain. No trusted intermediary.

---

## Quick Start — Node.js

### Install

```bash
npm install @apeiron/sdk
```

### Protect your API (Express)

```javascript
const { withX402 } = require('@apeiron/sdk');

app.get('/api/data', withX402(
  async (req, res) => {
    // If you reach here, payment is verified on-chain
    res.json({ data: "Premium content", paidBy: req.x402.wallet });
  },
  {
    contentUrl: 'https://yourapi.com/api/data',  // unique URL identifier
    // price and gateway read from .env
  }
));
```

### Environment variables

```bash
X402_GATEWAY_ADDRESS=0x994De1C65DaA8c852542eFdc56163E667C50f364
X402_USDC_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
X402_RPC_URL=https://mainnet.base.org
X402_CONTENT_URL=https://yourapi.com/api/data
```

### Agent that pays automatically

```javascript
const { AgentWallet } = require('@apeiron/sdk');

const agent = new AgentWallet({
  privateKey: process.env.AGENT_PRIVATE_KEY,
});

// Automatically detects 402, pays, retries
const data = await agent.fetch('https://yourapi.com/api/data');
console.log(data);
```

---

## Quick Start — Python

### Install

```bash
pip install apeiron-sdk
```

### Protect your API (Flask)

```python
from apeiron_sdk import with_x402

@app.route('/api/data')
@with_x402(content_url='https://yourapi.com/api/data')
def get_data():
    # If you reach here, payment is verified on-chain
    x402 = request.environ['x402']
    return jsonify({"data": "Premium content", "paidBy": x402['wallet']})
```

### Agent that pays automatically

```python
from apeiron_sdk import AgentWallet

agent = AgentWallet()  # reads AGENT_PRIVATE_KEY from .env

# Automatically detects 402, pays, retries
data = agent.fetch('https://yourapi.com/api/data')
print(data)
```

---

## Register your content

Before accepting payments, register your content URL on the smart contract.
You only need to do this once per endpoint.

```javascript
const { ethers } = require('ethers');

const GATEWAY_ABI = [
  "function registerContent(bytes32 contentId, uint256 humanPrice, uint256 agentPrice, string calldata contentURI) external"
];

const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
const signer   = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
const gateway  = new ethers.Contract(GATEWAY_ADDRESS, GATEWAY_ABI, signer);

const contentId = ethers.keccak256(ethers.toUtf8Bytes('https://yourapi.com/api/data'));

await gateway.registerContent(
  contentId,
  100000,     // 0.10 USDC for humans (6 decimals)
  1000000,    // 1.00 USDC for AI agents (6 decimals)
  'https://yourapi.com/api/data'
);
```

---

## Pricing

USDC uses 6 decimals:

| Amount | Units |
|--------|-------|
| $0.01 USDC | 10,000 |
| $0.10 USDC | 100,000 |
| $1.00 USDC | 1,000,000 |
| $50.00 USDC | 50,000,000 |

---

## Smart Contract

Deployed on **Base Mainnet** (chainId: 8453):

| Contract | Address |
|----------|---------|
| X402Gateway | `0x994De1C65DaA8c852542eFdc56163E667C50f364` |
| USDC (Base) | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

[View on BaseScan](https://basescan.org/address/0x994De1C65DaA8c852542eFdc56163E667C50f364)

**Revenue split**: 90% to publisher, 10% platform fee — distributed instantly on every payment.

---

## Access Types

| Type | Value | Who |
|------|-------|-----|
| `READ_ONLY` | 0 | Human readers |
| `DATA_MINING_LICENSED` | 1 | AI agents / crawlers |

AI agents receive an on-chain receipt proving they have a valid license — protecting them from copyright claims.

---

## Full Example

Clone and run the demo:

```bash
git clone https://github.com/apeiron-protocol/sdk
cd sdk/sdk-node
cp .env.example .env
# Add your PRIVATE_KEY to .env

# Terminal 1 — start the server
node example-server.js

# Terminal 2 — run the agent
node example-agent.js
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Your API Server                    │
│                                                      │
│   app.get('/data', withX402(handler, options))       │
│                    │                                 │
│                    ▼                                 │
│   ┌─────────────────────────────────────────┐       │
│   │           Apeiron Middleware             │       │
│   │                                         │       │
│   │  1. Check User-Agent (human vs bot)     │       │
│   │  2. No wallet → respond 402             │       │
│   │  3. Wallet present → verify on-chain    │       │
│   │  4. Verified → call your handler        │       │
│   └─────────────────────────────────────────┘       │
│                    │                                 │
│                    ▼                                 │
│         Base Blockchain (hasAccess)                  │
└─────────────────────────────────────────────────────┘
```

---

## Roadmap

- [x] Node.js SDK (server + client)
- [x] Python SDK (server + client)
- [ ] Dashboard for publishers
- [ ] AI model aggregator (OpenAI, Anthropic, Groq — one USDC balance)
- [ ] WordPress plugin
- [ ] Subscription model (pay-per-month cap)

---

## License

MIT © Apeiron Protocol

---

## Contributing

PRs welcome. Open an issue first to discuss what you would like to change.
