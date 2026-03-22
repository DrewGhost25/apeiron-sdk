require("dotenv").config();
const express = require("express");
const { withX402 } = require("./server");

const app = express();

// Dati premium protetti da x402
const premiumData = {
  title: "Dataset Prezzi Immobili Milano 2026",
  records: [
    { zona: "Brera",      prezzo_mq: 12500, trend: "+3.2%" },
    { zona: "Navigli",    prezzo_mq: 8900,  trend: "+1.8%" },
    { zona: "Porta Nuova",prezzo_mq: 11200, trend: "+4.1%" },
    { zona: "Isola",      prezzo_mq: 7800,  trend: "+2.5%" },
    { zona: "Duomo",      prezzo_mq: 15000, trend: "+2.9%" },
  ],
  updated: "2026-03-17",
  source:  "X402 Demo Dataset",
};

// Route pubblica — preview gratuita
app.get("/data/preview", (req, res) => {
  res.json({
    title:   premiumData.title,
    records: premiumData.records.slice(0, 1),
    note:    "Solo 1 record gratuito. Paga 0.05 USDC per il dataset completo.",
  });
});

// Route premium — protetta da x402
app.get("/data/full", withX402(
  async (req, res) => {
    res.json({
      ...premiumData,
      accessedBy: req.x402.wallet,
      accessType: req.x402.accessType === 1 ? "AI_LICENSE" : "HUMAN_READ",
    });
  },
  {
    gatewayAddress: process.env.X402_GATEWAY_ADDRESS,
    contentUrl:     process.env.X402_CONTENT_URL,
    price:          0.05,
  }
));

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`\n✅ Server x402 in ascolto su http://localhost:${PORT}`);
  console.log(`   Preview: http://localhost:${PORT}/data/preview`);
  console.log(`   Premium: http://localhost:${PORT}/data/full`);
});
