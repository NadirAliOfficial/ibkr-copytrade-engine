from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)
orders = []

@app.route('/order', methods=['POST'])
def receive():
    data = request.json
    data['id'] = str(uuid.uuid4())   # unique ID for every order
    orders.append(data)
    print("Received:", data)
    return jsonify({"status": "ok", "id": data['id']})

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

@app.route('/clear', methods=['POST'])
def clear():
    orders.clear()
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)