from ib_insync import IB, util
from flask import Flask, request, jsonify
import threading
import uuid
import time

# ── config ────────────────────────────────────────────────────────────────────
TWS_HOST   = "127.0.0.1"
TWS_PORT   = 7497         # 7496 = Live TWS | 7497 = Paper TWS
TWS_CLIENT = 0             # clientId=0 sees ALL manual orders placed in TWS
FLASK_PORT = 5001

# ── shared state ──────────────────────────────────────────────────────────────
orders         = []        # list of all captured orders
sent_keys      = set()     # dedup: avoid sending same order twice
master_balance = 0.0       # master account net liquidation value
lock           = threading.Lock()

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/orders", methods=["GET"])
def get_orders():
    """
    Clients poll this endpoint.
    Supports ?since=N to get only new orders from index N onwards.
    """
    since = request.args.get("since", 0, type=int)
    with lock:
        return jsonify({
            "orders":         orders[since:],
            "master_balance": master_balance,
            "total":          len(orders),
        })

@app.route("/balance", methods=["GET"])
def get_balance():
    return jsonify({"master_balance": master_balance})

@app.route("/clear", methods=["POST"])
def clear_orders():
    with lock:
        orders.clear()
        sent_keys.clear()
    print("🗑️  Orders cleared")
    return jsonify({"status": "cleared"})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status":         "running",
        "total_orders":   len(orders),
        "master_balance": master_balance,
    })

# ── position capture (ALL existing positions — no time/age limit) ─────────────
def capture_positions(ib):
    """
    Fetch ALL current positions from TWS.
    Unlike reqOpenOrders() which only returns active/pending orders,
    ib.positions() returns every open position in the account regardless
    of when the trade was originally placed — no 24-hour limit.

    We call reqPositions() first and sleep to give TWS enough time
    to stream all position data before reading it. Without this,
    ib.positions() may only return a partial list (typically the
    most recent ones).
    """
    print("📦  Requesting all positions from TWS...")
    try:
        ib.reqPositions()
        ib.sleep(5)  # give TWS time to stream all positions
    except Exception as e:
        print(f"⚠️  reqPositions failed: {e}")
        return

    try:
        positions = ib.positions()
    except Exception as e:
        print(f"⚠️  Failed to read positions: {e}")
        return

    if not positions:
        print("📦  No existing positions found.")
        return

    loaded = 0
    with lock:
        for pos in positions:
            c = pos.contract
            qty = float(pos.position)

            # skip zero-quantity positions
            if qty == 0:
                continue

            key = f"POS-{c.symbol}-{pos.account}"
            if key in sent_keys:
                continue
            sent_keys.add(key)

            order_data = {
                "id":        str(uuid.uuid4()),
                "symbol":    c.symbol,
                "exchange":  c.exchange or "SMART",
                "currency":  c.currency or "USD",
                "action":    "BUY" if qty > 0 else "SELL",
                "orderType": "MKT",
                "quantity":  abs(qty),
                "price":     float(pos.avgCost),
            }
            orders.append(order_data)
            loaded += 1
            print(f"📦  Position: {c.symbol} qty={qty} avgCost={pos.avgCost}")

    print(f"📦  Loaded {loaded} positions (out of {len(positions)} total)")

# ── TWS order capture (live order events) ──────────────────────────────────────
def capture(trade):
    o = trade.order
    c = trade.contract

    # dedup key — orderId is unique per order in TWS
    key = f"{o.orderId}-{c.symbol}-{o.action}-{o.totalQuantity}"
    with lock:
        if key in sent_keys:
            return
        sent_keys.add(key)

        order_data = {
            "id":        str(uuid.uuid4()),   # unique UUID for client dedup
            "symbol":    c.symbol,
            "exchange":  c.exchange or "SMART",
            "currency":  c.currency or "USD",
            "action":    o.action,
            "orderType": o.orderType,
            "quantity":  float(o.totalQuantity),
            "price":     float(o.lmtPrice) if o.lmtPrice else 0.0,
        }
        orders.append(order_data)

    print(f"✅  Captured [{len(orders)-1}]: {o.action} {c.symbol} "
          f"qty={float(o.totalQuantity)} @ {o.lmtPrice} ({o.orderType})")

# ── balance updater ───────────────────────────────────────────────────────────
def update_balance(ib):
    global master_balance
    try:
        for v in ib.accountValues():
            if v.tag == "NetLiquidation" and v.currency == "USD":
                master_balance = float(v.value)
                print(f"💰  Master balance: ${master_balance:,.2f}")
                return
    except Exception as e:
        print(f"⚠️  Balance fetch failed: {e}")

def balance_loop(ib):
    """Update master balance every 30 seconds."""
    while True:
        update_balance(ib)
        time.sleep(30)

# ── TWS connection ─────────────────────────────────────────────────────────────
def start_tws():
    util.startLoop()  # required for ib_insync background mode

def connect_tws():
    ib = IB()
    print(f"🔌  Connecting to TWS {TWS_HOST}:{TWS_PORT} clientId={TWS_CLIENT} ...")
    ib.connect(TWS_HOST, TWS_PORT, clientId=TWS_CLIENT)
    print("✅  TWS connected")

    # fetch initial balance
    update_balance(ib)

    # ── load ALL existing positions (no time/age limit) ───────────────────
    capture_positions(ib)

    # start balance updater thread
    t = threading.Thread(target=balance_loop, args=(ib,), daemon=True)
    t.start()

    # hook order events for NEW orders going forward
    ib.newOrderEvent    += capture
    ib.orderStatusEvent += capture
    ib.openOrderEvent   += capture

    # fetch existing open orders on startup
    ib.reqOpenOrders()
    ib.sleep(1)

    print(f"👂  Listening for orders on TWS...")
    print(f"🌐  Production server running on http://0.0.0.0:{FLASK_PORT}")
    print(f"     GET  /orders?since=N  — poll new orders")
    print(f"     GET  /balance         — master balance")
    print(f"     GET  /status          — server status")
    print(f"     POST /clear           — clear order list")
    ib.run()

# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start production WSGI server (waitress) in a background thread
    # Install once: pip install waitress
    from waitress import serve

    flask_thread = threading.Thread(
        target=lambda: serve(app, host="0.0.0.0", port=FLASK_PORT),
        daemon=True
    )
    flask_thread.start()
    print(f"🚀  Waitress production server started on port {FLASK_PORT}")

    # Connect to TWS (blocking — keeps process alive)
    connect_tws()