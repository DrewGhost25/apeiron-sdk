import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
import json
import requests
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

GATEWAY_ABI = [
    {
        "inputs": [
            {"name": "contentId", "type": "bytes32"},
            {"name": "duration", "type": "uint256"}
        ],
        "name": "unlockAsHuman",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "contentId", "type": "bytes32"},
            {"name": "duration", "type": "uint256"}
        ],
        "name": "unlockAsAgent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "user", "type": "address"},
            {"name": "contentId", "type": "bytes32"},
            {"name": "accessType", "type": "uint8"}
        ],
        "name": "hasAccess",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

USDC_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class AgentWallet:
    """
    Client Python che paga automaticamente le API protette da x402.

    Uso:
        agent = AgentWallet(private_key="0x...")
        data  = agent.fetch("http://localhost:5000/data/full")
    """

    def __init__(
        self,
        private_key=None,
        rpc_url=None,
        usdc_address=None,
        user_agent="X402-Agent/1.0 (bot)",
        verbose=True
    ):
        self.private_key  = private_key or os.getenv('X402_AGENT_PRIVATE_KEY')
        self.rpc_url      = rpc_url     or os.getenv('X402_RPC_URL', 'https://mainnet.base.org')
        self.usdc_address = usdc_address or os.getenv('X402_USDC_ADDRESS', '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913')
        self.user_agent   = user_agent
        self.verbose      = verbose

        if not self.private_key:
            raise ValueError("AgentWallet: private_key richiesta")

        from requests import Session
        session = Session()
        session.verify = False
        self.w3      = Web3(Web3.HTTPProvider(self.rpc_url, session=session))
        self.account = Account.from_key(self.private_key)

    def log(self, msg):
        if self.verbose:
            print(msg)

    @property
    def address(self):
        return self.account.address

    def balance(self):
        """Ritorna il saldo USDC del wallet agente."""
        usdc = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.usdc_address),
            abi=USDC_ABI
        )
        bal = usdc.functions.balanceOf(self.account.address).call()
        return bal / 1_000_000

    def fetch(self, url, headers=None):
        """
        Chiama una API protetta da x402 e paga automaticamente se necessario.
        """
        headers = headers or {}
        headers['User-Agent'] = self.user_agent

        # STEP 1 — Prima chiamata senza wallet
        self.log(f"\n[x402] → GET {url}")
        res1 = requests.get(url, headers=headers,verify=False)

        # Accesso diretto
        if res1.status_code == 200:
            self.log("[x402] ✓ Accesso diretto (nessun pagamento necessario)")
            return res1.json()

        # Risposta inattesa
        if res1.status_code != 402:
            raise Exception(f"[x402] Risposta inattesa: {res1.status_code}")

        # STEP 2 — Leggi istruzioni dal 402
        payment = res1.json()
        self.log(f"[x402] ← 402 Payment Required")
        self.log(f"[x402]   contentId:  {payment['contentId']}")
        self.log(f"[x402]   price:      {payment['priceFormatted']}")
        self.log(f"[x402]   accessType: {payment['accessType']}")

        # STEP 3 — Verifica saldo
        usdc    = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.usdc_address),
            abi=USDC_ABI
        )
        price_units = int(payment['price'])
        balance     = usdc.functions.balanceOf(self.account.address).call()
        self.log(f"[x402]   saldo USDC: {balance / 1_000_000:.2f} USDC")

        if balance < price_units:
            raise Exception(
                f"[x402] Saldo insufficiente. Hai {balance / 1_000_000} USDC, servono {price_units / 1_000_000} USDC"
            )

        # STEP 4 — Approve USDC
        self.log(f"[x402] → USDC.approve({price_units} units)...")
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        approve_tx = usdc.functions.approve(
            Web3.to_checksum_address(payment['gatewayAddress']),
            price_units
        ).build_transaction({
            'from':     self.account.address,
            'nonce':    nonce,
            'gas':      100000,
            'gasPrice': 2000000000,
            'chainId':  8453
        })
        signed   = self.w3.eth.account.sign_transaction(approve_tx, self.private_key)
        tx_hash  = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt  = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.log(f"[x402] ✓ Approve confermato — tx: {tx_hash.hex()}")

        # Aspetta che l'approve sia completamente confermato
        import time
        time.sleep(3)

        # STEP 5 — Paga licenza
        gateway   = self.w3.eth.contract(
            address=Web3.to_checksum_address(payment['gatewayAddress']),
            abi=GATEWAY_ABI
        )
        is_agent   = payment['accessType'] == 'AI_LICENSE'
        content_id = bytes.fromhex(payment['contentId'][2:])

        self.log(f"[x402] → gateway.{'unlockAsAgent' if is_agent else 'unlockAsHuman'}()...")
        nonce = self.w3.eth.get_transaction_count(self.account.address,'pending')

        if is_agent:
            pay_fn = gateway.functions.unlockAsAgent(content_id, 30 * 24 * 60 * 60)
        else:
            pay_fn = gateway.functions.unlockAsHuman(content_id, 0)

        pay_tx = pay_fn.build_transaction({
            'from':     self.account.address,
            'nonce':    nonce,
            'gas':      200000,
            'gasPrice': 2000000000, 
            'chainId':  8453
        })
        """
        self.w3.eth.gas_price*2
        """

        signed  = self.w3.eth.account.sign_transaction(pay_tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        self.log(f"[x402] ✓ Licenza emessa — tx: {tx_hash.hex()}")

        # STEP 6 — Riaccesso con wallet
        import time
        time.sleep(5)
        self.log(f"[x402] → Riaccesso con wallet {self.address}...")
        headers['X-Wallet-Address'] = self.address
        res2 = requests.get(url, headers=headers, verify=False)

        if res2.status_code != 200:
            raise Exception(f"[x402] Accesso negato dopo pagamento: {res2.status_code}")

        self.log("[x402] ✓ Contenuto ricevuto con licenza!")
        return res2.json()