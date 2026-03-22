import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import os
import re
from functools import wraps
from web3 import Web3
from flask import Flask, request, jsonify

# ABI minimo del contratto
GATEWAY_ABI = [
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
    },
    {
        "inputs": [{"name": "contentId", "type": "bytes32"}],
        "name": "getContent",
        "outputs": [
            {"name": "publisher", "type": "address"},
            {"name": "humanPrice", "type": "uint256"},
            {"name": "agentPrice", "type": "uint256"},
            {"name": "active", "type": "bool"},
            {"name": "contentURI", "type": "string"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

KNOWN_BOTS = re.compile(
    r'GPTBot|ClaudeBot|Google-Extended|anthropic|openai|bot|crawler|spider|X402-Agent',
    re.IGNORECASE
)

def with_x402(content_url=None, gateway_address=None, usdc_address=None, rpc_url=None):
    """
    Decorator che protegge una route Flask con pagamento USDC x402.

    Uso:
        @app.route('/data/full')
        @with_x402(content_url='http://localhost:5000/data/full')
        def get_data():
            wallet = request.x402['wallet']
            return jsonify({"data": "contenuto premium"})
    """
    _gateway = gateway_address or os.getenv('X402_GATEWAY_ADDRESS')
    _usdc    = usdc_address    or os.getenv('X402_USDC_ADDRESS', '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913')
    _rpc     = rpc_url         or os.getenv('X402_RPC_URL', 'https://mainnet.base.org')
    _url     = content_url     or os.getenv('X402_CONTENT_URL')

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_agent  = request.headers.get('User-Agent', '')
            wallet      = request.headers.get('X-Wallet-Address') or request.args.get('wallet')
            is_bot      = bool(KNOWN_BOTS.search(user_agent))
            access_type = 1 if is_bot else 0

            print(f"[x402 debug] user_agent={user_agent[:30]} wallet={wallet} is_bot={is_bot}")

            # Connetti a Base
            from requests import Session
            session = Session()
            session.verify = False
            w3 = Web3(Web3.HTTPProvider(_rpc,session=session))
            gateway = w3.eth.contract(
                address=Web3.to_checksum_address(_gateway),
                abi=GATEWAY_ABI
            )
            content_id = Web3.keccak(text=_url)

            # Nessun wallet → rispondi 402
            if not wallet:
                content = gateway.functions.getContent(content_id).call()
                price = content[2] if is_bot else content[1]  # agentPrice o humanPrice

                return jsonify({
                    'error':          'Payment Required',
                    'protocol':       'x402',
                    'version':        '1.0',
                    'gatewayAddress': _gateway,
                    'usdcAddress':    _usdc,
                    'contentId':      '0x' + content_id.hex(),
                    'accessType':     'AI_LICENSE' if is_bot else 'HUMAN_READ',
                    'price':          str(price),
                    'priceFormatted': f"{price / 1_000_000:.6f} USDC",
                    'instructions': {
                        'step1': f'USDC.approve("{_gateway}", {price})',
                        'step2': f'gateway.unlockAsAgent("0x{content_id.hex()}", 2592000)' if is_bot
                                 else f'gateway.unlockAsHuman("0x{content_id.hex()}", 0)'
                    },
                    'network': {'name': 'Base', 'chainId': 8453}
                }), 402

            # Wallet presente → verifica on-chain
            has_access = gateway.functions.hasAccess(
                Web3.to_checksum_address(wallet),
                content_id,
                access_type
            ).call()

            if not has_access:
                return jsonify({
                    'error':     'Payment Required',
                    'reason':    'No valid access found on-chain',
                    'wallet':    wallet,
                    'contentId': '0x' + content_id.hex()
                }), 402

            # Accesso verificato → aggiungi info alla request e chiama handler
            request.environ['x402'] = {
                'wallet':      wallet,
                'content_id':  '0x' + content_id.hex(),
                'access_type': access_type,
                'verified':    True
            }
            return f(*args, **kwargs)

        return wrapper
    return decorator