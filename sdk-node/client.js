process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const { ethers } = require("ethers");

const GATEWAY_ABI = [
  "function unlockAsHuman(bytes32 contentId, uint256 duration) external",
  "function unlockAsAgent(bytes32 contentId, uint256 duration) external",
  "function hasAccess(address user, bytes32 contentId, uint8 accessType) external view returns (bool)",
];

const USDC_ABI = [
  "function approve(address spender, uint256 amount) external returns (bool)",
  "function balanceOf(address account) external view returns (uint256)",
];

/**
 * AgentWallet — client che paga automaticamente le API protette da x402
 *
 * Uso:
 *   const agent = new AgentWallet({ privateKey: "0x..." });
 *   const data  = await agent.fetch("https://api.example.com/data");
 */
class AgentWallet {
  constructor(options = {}) {
    const {
      privateKey = process.env.X402_AGENT_PRIVATE_KEY,
      rpcUrl     = process.env.X402_RPC_URL || "https://mainnet.base.org",
      usdcAddress = process.env.X402_USDC_ADDRESS || "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      userAgent  = "X402-Agent/1.0 (bot)",
      verbose    = true,
    } = options;

    if (!privateKey) throw new Error("AgentWallet: privateKey richiesta");

    this.provider    = new ethers.JsonRpcProvider(rpcUrl);
    this.wallet      = new ethers.Wallet(privateKey, this.provider);
    this.usdcAddress = usdcAddress;
    this.userAgent   = userAgent;
    this.verbose     = verbose;
    this.log         = verbose ? console.log : () => {};
  }

  get address() {
    return this.wallet.address;
  }

  /**
   * fetch() — chiama una API protetta da x402 e paga automaticamente se necessario
   *
   * @param {string} url      URL dell'API
   * @param {Object} options  Opzioni fetch standard + { asBot: true }
   * @returns {Object}        Risposta JSON dell'API
   */
  async fetch(url, options = {}) {
    const { asBot = true, ...fetchOptions } = options;
    const fetch = (...args) => import("node-fetch").then(({ default: f }) => f(...args));

    // STEP 1 — Prima chiamata senza wallet
    this.log(`\n[x402] → GET ${url}`);
    const res1 = await fetch(url, {
      ...fetchOptions,
      headers: {
        "User-Agent": this.userAgent,
        ...fetchOptions.headers,
      },
    });

    // Accesso diretto — nessun pagamento necessario
    if (res1.status === 200) {
      this.log(`[x402] ✓ Accesso diretto (nessun pagamento necessario)`);
      return res1.json();
    }

    // Risposta inattesa
    if (res1.status !== 402) {
      throw new Error(`[x402] Risposta inattesa: ${res1.status}`);
    }

    // STEP 2 — Leggi istruzioni dal 402
    const body402 = await res1.text();
    const payment = JSON.parse(body402);

    this.log(`[x402] ← 402 Payment Required`);
    this.log(`[x402]   contentId:  ${payment.contentId}`);
    this.log(`[x402]   price:      ${payment.priceFormatted}`);
    this.log(`[x402]   accessType: ${payment.accessType}`);

    // STEP 3 — Verifica saldo USDC
    const usdc    = new ethers.Contract(this.usdcAddress, USDC_ABI, this.wallet);
    const priceBI = BigInt(payment.price);
    const balance = await usdc.balanceOf(this.wallet.address);
    this.log(`[x402]   saldo USDC: ${(Number(balance) / 1_000_000).toFixed(2)} USDC`);

    if (balance < priceBI) {
      throw new Error(
        `[x402] Saldo USDC insufficiente. Hai ${Number(balance) / 1_000_000} USDC, servono ${Number(payment.price) / 1_000_000} USDC`
      );
    }

    // STEP 4 — Approve USDC
   
    console.log("[x402 debug] price type:", typeof payment.price, "value:", payment.price);
    console.log("[x402 debug] priceBI:", priceBI.toString());
    this.log(`[x402] → USDC.approve(${payment.price} units)...`);
    const approveTx = await usdc.approve(payment.gatewayAddress, priceBI);
    await approveTx.wait();
    this.log(`[x402] ✓ Approve confermato — tx: ${approveTx.hash}`);

    // STEP 5 — Paga licenza
    const gateway = new ethers.Contract(payment.gatewayAddress, GATEWAY_ABI, this.wallet);
    const isAgent = payment.accessType === "AI_LICENSE";

    this.log(`[x402] → gateway.${isAgent ? "unlockAsAgent" : "unlockAsHuman"}()...`);
    const payTx = isAgent
      ? await gateway.unlockAsAgent(payment.contentId, 30 * 24 * 60 * 60)
      : await gateway.unlockAsHuman(payment.contentId, 0);
    await payTx.wait();
    this.log(`[x402] ✓ Licenza emessa — tx: ${payTx.hash}`);

    // STEP 6 — Richiama con wallet
    this.log(`[x402] → Riaccesso con wallet ${this.wallet.address}...`);
    const res2 = await fetch(url, {
      ...fetchOptions,
      headers: {
        "User-Agent": this.userAgent,
        "x-wallet-address": this.wallet.address,
        ...fetchOptions.headers,
      },
    });

    if (res2.status !== 200) {
      throw new Error(`[x402] Accesso negato dopo pagamento: ${res2.status}`);
    }

    this.log(`[x402] ✓ Contenuto ricevuto con licenza!`);
    return res2.json();
  }

  /**
   * balance() — ritorna il saldo USDC del wallet agente
   */
  async balance() {
    const usdc    = new ethers.Contract(this.usdcAddress, USDC_ABI, this.wallet);
    const balance = await usdc.balanceOf(this.wallet.address);
    return Number(balance) / 1_000_000;
  }
}

module.exports = { AgentWallet };