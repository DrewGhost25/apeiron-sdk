require("dotenv").config();
const { AgentWallet } = require("./client");

async function main() {
  console.log("🤖 X402 AgentWallet Demo");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

  const agent = new AgentWallet({
    privateKey: process.env.X402_AGENT_PRIVATE_KEY,
    verbose:    true,
  });

  console.log("Wallet agente:", agent.address);

  // Controlla saldo USDC
  const balance = await agent.balance();
  console.log("Saldo USDC:   ", balance, "USDC");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

  try {
    // Prima chiama la preview gratuita
    console.log("\n📄 Chiamata preview gratuita...");
    const fetch = (...args) => import("node-fetch").then(({ default: f }) => f(...args));
    const preview = await fetch("http://localhost:4000/data/preview");
    const previewData = await preview.json();
    console.log("Preview:", JSON.stringify(previewData, null, 2));

    // Poi chiama il dataset completo — paga automaticamente se necessario
    console.log("\n💎 Chiamata dataset completo (x402)...");
    const data = await agent.fetch("http://localhost:4000/data/full");

    console.log("\n✅ Dataset completo ricevuto!");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    console.log(JSON.stringify(data, null, 2));

  } catch (err) {
    console.error("\n❌ Errore:", err.message);
  }
}

main().catch(console.error);
