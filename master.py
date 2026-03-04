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
orders           = []
sent_keys        = set()
master_balance   = 0.0
positions_cache  = []      # refreshed every 30s by background loop — thread-safe snapshot
_ib_instance     = None
lock             = threading.Lock()

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/orders", methods=["GET"])
def get_orders():
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

@app.route("/positions", methods=["GET"])
def get_positions():
    """
    Serves the positions_cache snapshot — updated every 30s by the IB background loop.
    Never calls IB directly (avoids asyncio event loop errors in Waitress threads).
    """
    global _ib_instance
    if _ib_instance is None or not _ib_instance.isConnected():
        return jsonify({"positions": [], "error": "not_connected"})
    with lock:
        return jsonify({"positions": list(positions_cache)})

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

# ── position capture on startup ───────────────────────────────────────────────
def capture_positions(ib):
    print("📦  Requesting all positions from TWS...")
    try:
        ib.reqPositions()
        ib.sleep(5)
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

# ── TWS order capture ─────────────────────────────────────────────────────────
def capture(trade):
    o = trade.order
    c = trade.contract
    key = f"{o.orderId}-{c.symbol}-{o.action}-{o.totalQuantity}"
    with lock:
        if key in sent_keys:
            return
        sent_keys.add(key)
        order_data = {
            "id":        str(uuid.uuid4()),
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

def update_positions_cache(ib):
    """Refresh positions_cache from IB — called from the IB event loop thread only."""
    global positions_cache
    try:
        snapshot = []
        for p in ib.portfolio():
            qty = float(p.position)
            if qty == 0:
                continue
            snapshot.append({
                "symbol":   p.contract.symbol,
                "currency": p.contract.currency or "USD",
                "exchange": p.contract.exchange or "SMART",
                "quantity": abs(qty),
                "side":     "BUY" if qty > 0 else "SELL",
            })
        with lock:
            positions_cache.clear()
            positions_cache.extend(snapshot)
        print(f"📊  Positions cache updated: {len(snapshot)} positions")
    except Exception as e:
        print(f"⚠️  Positions cache update failed: {e}")


def balance_loop(ib):
    while True:
        update_balance(ib)
        update_positions_cache(ib)
        time.sleep(30)

# ── TWS connection ─────────────────────────────────────────────────────────────
def connect_tws():
    global _ib_instance
    ib = IB()
    _ib_instance = ib
    print(f"🔌  Connecting to TWS {TWS_HOST}:{TWS_PORT} clientId={TWS_CLIENT} ...")
    ib.connect(TWS_HOST, TWS_PORT, clientId=TWS_CLIENT)
    print("✅  TWS connected")

    update_balance(ib)
    capture_positions(ib)
    update_positions_cache(ib)   # populate cache immediately on startup

    t = threading.Thread(target=balance_loop, args=(ib,), daemon=True)
    t.start()

    ib.newOrderEvent    += capture
    ib.orderStatusEvent += capture
    ib.openOrderEvent   += capture

    ib.reqOpenOrders()
    ib.sleep(1)

    print(f"👂  Listening for orders on TWS...")
    print(f"🌐  Production server running on http://0.0.0.0:{FLASK_PORT}")
    print(f"     GET  /orders?since=N  — poll new orders")
    print(f"     GET  /balance         — master balance")
    print(f"     GET  /positions       — current open positions (for sync)")
    print(f"     GET  /status          — server status")
    print(f"     POST /clear           — clear order list")
    ib.run()

# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from waitress import serve
    flask_thread = threading.Thread(
        target=lambda: serve(app, host="0.0.0.0", port=FLASK_PORT),
        daemon=True
    )
    flask_thread.start()
    print(f"🚀  Waitress production server started on port {FLASK_PORT}")
    connect_tws()