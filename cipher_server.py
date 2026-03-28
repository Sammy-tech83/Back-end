from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/analyze', methods=['POST'])
def analyze():
    if not ANTHROPIC_API_KEY:
        return jsonify({'error': 'API key not configured on server'}), 500
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 600,
                'messages': [{'role': 'user', 'content': prompt}]
            }
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/prices', methods=['GET'])
def prices():
    try:
        page = int(request.args.get('page', 1))
        limit = 100
        offset = (page - 1) * limit
        url = f'https://api.coincap.io/v2/assets?limit={limit}&offset={offset}'
        response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
        data = response.json().get('data', [])
        # Normalize to match expected format
        normalized = [{
            'id': c.get('id'),
            'symbol': c.get('symbol', '').upper(),
            'name': c.get('name'),
            'current_price': float(c.get('priceUsd') or 0),
            'price_change_percentage_24h': float(c.get('changePercent24Hr') or 0),
            'high_24h': float(c.get('priceUsd') or 0) * 1.02,
            'low_24h': float(c.get('priceUsd') or 0) * 0.98,
            'market_cap_rank': int(c.get('rank') or 999),
        } for c in data]
        return jsonify(normalized)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'CIPHER server online'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
