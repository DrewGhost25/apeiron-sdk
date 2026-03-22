import os
from client import AgentWallet
from dotenv import load_dotenv
import requests

load_dotenv()

def main():
    print("🤖 X402 AgentWallet Python Demo")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    agent = AgentWallet(verbose=True)

    print(f"Wallet agente: {agent.address}")
    print(f"Saldo USDC:    {agent.balance():.2f} USDC")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Preview gratuita
    print("\n📄 Chiamata preview gratuita...")
    preview = requests.get("http://127.0.0.1:5001/data/preview",verify=False)
    print("Preview status:", preview.status_code)
    print("Preview text:", preview.text[:200])
    import json
    print("Preview:", json.dumps(preview.json(), indent=2, ensure_ascii=False))

    # Dataset completo — paga automaticamente
    print("\n💎 Chiamata dataset completo (x402)...")
    try:
        data = agent.fetch("http://127.0.0.1:5001/data/full")
        print("\n✅ Dataset completo ricevuto!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ Errore: {e}")

if __name__ == '__main__':
    main()