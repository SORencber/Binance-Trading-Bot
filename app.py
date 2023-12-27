# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import bot 
import coinlistele
app = Flask(__name__)
CORS(app)


@app.route('/start_bot', methods=['POST'])
def start_aibot():
    data = request.get_json()
    symbol = data.get('symbol', 'BTCUSDT')
    interval = data.get('interval', bot.client.KLINE_INTERVAL_1MINUTE)

    results = bot.run_bot()
    
    return jsonify(results)
@app.route('/start_analyst', methods=['POST'])
def start_analyst():
    data = request.get_json()
    symbol = data.get('symbol', 'BTCUSDT')
    interval = data.get('interval', bot.client.KLINE_INTERVAL_1MINUTE)

    results = coinlistele.main()
    
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
