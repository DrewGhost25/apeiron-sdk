import os
from flask import Flask, request, jsonify, g
from x402_server import with_x402
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

premium_data = {
    "title": "Dataset Prezzi Immobili Milano 2026",
    "records": [
        {"zona": "Brera",       "prezzo_mq": 12500, "trend": "+3.2%"},
        {"zona": "Navigli",     "prezzo_mq": 8900,  "trend": "+1.8%"},
        {"zona": "Porta Nuova", "prezzo_mq": 11200, "trend": "+4.1%"},
        {"zona": "Isola",       "prezzo_mq": 7800,  "trend": "+2.5%"},
        {"zona": "Duomo",       "prezzo_mq": 15000, "trend": "+2.9%"},
    ],
    "updated": "2026-03-17",
    "source":  "X402 Demo Dataset"
}

# Route pubblica — preview gratuita
@app.route('/data/preview')
def preview():
    return jsonify({
        "title":   premium_data["title"],
        "records": premium_data["records"][:1],
        "note":    "Solo 1 record gratuito. Paga 0.05 USDC per il dataset completo."
    })

# Route premium — protetta da x402
@app.route('/data/full')
@with_x402(content_url='http://127.0.0.1:5001/data/full')
def full_data():
    x402 = request.environ['x402']
    return jsonify({
        **premium_data,
        "accessedBy":  x402['wallet'],
        "accessType":  "AI_LICENSE" if x402['access_type'] == 1 else "HUMAN_READ"
    })

if __name__ == '__main__':
    print("✅ Server x402 Python in ascolto su http://localhost:5001")
    app.run(port=5001, debug=False)