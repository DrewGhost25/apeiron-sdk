process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const { ethers } = require("ethers");

const GATEWAY_ABI = [
  "function hasAccess(address user, bytes32 contentId, uint8 accessType) external view returns (bool)",
  "function getContent(bytes32 contentId) external view returns (address publisher, uint256 humanPrice, uint256 agentPrice, bool active, string contentURI)",
];

const KNOWN_BOTS = /GPTBot|ClaudeBot|Google-Extended|anthropic|openai|bot|crawler|spider|X402-Agent/i;

/**
 * withX402 — middleware che protegge una route con pagamento USDC
 *
 * @param {Function} handler     La tua funzione API originale
 * @param {Object}   options     Configurazione
 * @param {number}   options.price        Prezzo in USDC (es. 0.05)
 * @param {string}   options.gatewayAddress  Indirizzo smart contract
 * @param {string}   options.usdcAddress     Indirizzo USDC su Base
 * @param {string}   options.contentUrl      URL univoco del contenuto
 * @param {string}   options.rpcUrl          RPC Base (default: mainnet)
 */
function withX402(handler, options = {}) {
  const {
    gatewayAddress = process.env.X402_GATEWAY_ADDRESS,
    usdcAddress    = process.env.X402_USDC_ADDRESS || "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    contentUrl     = process.env.X402_CONTENT_URL,
    rpcUrl         = process.env.X402_RPC_URL || "https://mainnet.base.org",
    price          = 0.05,
    currency       = "USDC",
  } = options;

  return async function x402Middleware(req, res) {
    try {
      const userAgent = req.headers["user-agent"] || "";
      const wallet    = req.headers["x-wallet-address"] || req.query.wallet;
      const isBot     = KNOWN_BOTS.test(userAgent);
      const accessType = isBot ? 1 : 0; // 1=AI, 0=human
      console.log("[x402 debug]", { userAgent: userAgent.slice(0,30), wallet, isBot, accessType });

      const provider  = new ethers.JsonRpcProvider(rpcUrl);
      const gateway   = new ethers.Contract(gatewayAddress, GATEWAY_ABI, provider);
      const contentId = ethers.keccak256(ethers.toUtf8Bytes(contentUrl));

      // Nessun wallet → rispondi 402 con istruzioni
      if (!wallet) {
        const content = await gateway.getContent(contentId);
        const priceUnits = isBot
          ? content.agentPrice.toString()
          : content.humanPrice.toString();

        return res.status(402).json({
          error:          "Payment Required",
          protocol:       "x402",
          version:        "1.0",
          gatewayAddress,
          usdcAddress,
          contentId,
          accessType:     isBot ? "AI_LICENSE" : "HUMAN_READ",
          price:          priceUnits,
          priceFormatted: (Number(priceUnits) / 1_000_000).toFixed(6) + " USDC",
          instructions: {
            step1: `USDC.approve("${gatewayAddress}", ${priceUnits})`,
            step2: isBot
              ? `gateway.unlockAsAgent("${contentId}", 2592000)`
              : `gateway.unlockAsHuman("${contentId}", 0)`,
          },
          network: { name: "Base", chainId: 8453 },
        });
      }

      // Wallet presente → verifica on-chain
      const hasAccess = await gateway.hasAccess(wallet, contentId, accessType);

      if (!hasAccess) {
        return res.status(402).json({
          error:   "Payment Required",
          reason:  "No valid access found on-chain for this wallet",
          wallet,
          contentId,
        });
      }

      // Accesso verificato → passa all'handler originale
      req.x402 = { wallet, contentId, accessType, verified: true };
      return handler(req, res);

    } catch (err) {
      console.error("[x402] Errore middleware:", err.message);
      return res.status(500).json({ error: "x402 internal error", detail: err.message });
    }
  };
}

module.exports = { withX402 };