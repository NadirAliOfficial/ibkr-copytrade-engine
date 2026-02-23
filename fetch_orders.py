from ib_insync import *
import requests
from dotenv import load_dotenv
import os
load_dotenv()

VPS_URL = os.getenv("VPS_URL")
ib = IB()
ib.connect('127.0.0.1', 7496, clientId=0)  # 0 = sees ALL manual orders

sent = set()

def send(trade):
    o, c = trade.order, trade.contract
    key = f"{o.orderId}-{c.symbol}-{o.action}"
    if key in sent:
        return
    sent.add(key)
    try:
        requests.post(VPS_URL, json={
            "symbol": c.symbol,
            "exchange": c.exchange,
            "currency": c.currency,
            "action": o.action,
            "orderType": o.orderType,
            "quantity": float(o.totalQuantity),
            "price": o.lmtPrice,
        }, timeout=3)
        print(f"✅ Sent: {o.action} {c.symbol} qty={float(o.totalQuantity)} price={o.lmtPrice}")
    except Exception as e:
        print("❌ Failed:", e)

ib.newOrderEvent += send
ib.orderStatusEvent += send
ib.openOrderEvent += send

ib.reqOpenOrders()
ib.sleep(1)

print("Listening...")
ib.run()