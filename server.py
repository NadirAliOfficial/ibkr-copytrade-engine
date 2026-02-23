from flask import Flask, request, jsonify

app = Flask(__name__)
orders = []

@app.route('/order', methods=['POST'])
def receive():
    orders.append(request.json)
    print("Received:", request.json)
    return jsonify({"status": "ok"})

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
