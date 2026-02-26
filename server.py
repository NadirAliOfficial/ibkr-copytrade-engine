from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)
orders = []

@app.route('/order', methods=['POST'])
def receive():
    data = request.json
    data['id'] = str(uuid.uuid4())
    orders.append(data)
    print(f"Received [{len(orders)-1}]: {data['symbol']} {data['action']} {data['quantity']}")
    return jsonify({"status": "ok", "id": data['id']})

@app.route('/orders', methods=['GET'])
def get_orders():
    # Client passes ?since=N to get only orders from index N onwards
    since = request.args.get('since', 0, type=int)
    return jsonify(orders[since:])

@app.route('/clear', methods=['POST'])
def clear():
    orders.clear()
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)