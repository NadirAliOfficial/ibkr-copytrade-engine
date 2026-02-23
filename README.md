# ⬡ NeroAI — IBKR CopyTrade Engine

> Mirror trades from a master IBKR account to unlimited client accounts in real-time.

![NeroAI](https://img.shields.io/badge/NeroAI-CopyTrade-00d4aa?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge)
![IBKR](https://img.shields.io/badge/Interactive%20Brokers-TWS-red?style=for-the-badge)

---

## How It Works

```
Master Account (Your Machine)
        │
        │  HTTP POST (real-time)
        ▼
    VPS Ubuntu (Relay Server)
        │
        │  HTTP GET (poll every 2s)
        ▼
Client .exe (Any Windows Machine)
        │
        ▼
  Client IBKR Account
```

---

## Project Structure

```
ibkr-copytrade-engine/
├── fetch_orders.py       # Runs on master machine — sends orders to VPS
├── server.py             # Runs on Ubuntu VPS — receives & stores orders
├── neroai_client.py      # Client GUI app — polls VPS & places orders
├── build_neroai.spec     # PyInstaller spec to build Windows .exe
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Setup

### 1. Master Machine (Your IBKR Account)

**Requirements:**
- TWS (Trader Workstation) running and logged in
- API enabled in TWS: `Edit → Global Config → API → Enable ActiveX and Socket Clients`

**Install:**
```bash
pip install ib_insync requests
```

**Run:**
```bash
python fetch_orders.py
```

This will connect to TWS, fetch all open orders on startup, then listen for new orders in real-time and forward them to your VPS.

---

### 2. VPS Ubuntu (Relay Server)

**Install:**
```bash
pip install flask
```

**Run:**
```bash
python server.py
```

Server runs on port `5000`. Make sure port 5000 is open in your VPS firewall.

**Endpoints:**
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/order` | Receives order from master machine |
| GET | `/orders` | Returns all orders (polled by clients) |

---

### 3. Client Machine (Windows .exe)

Clients need:
- **TWS** installed, running, and logged in to their IBKR account
- API enabled in TWS settings
- The `NeroAI_CopyTrade.exe` file

On startup, the client enters their TWS connection details and presses **START**. The app will automatically mirror all orders from the master account into their account.

---

## Building the Windows .exe

> Must be built on a Windows machine or via GitHub Actions (see below).

**On Windows:**
```bash
pip install pyinstaller ib_insync requests pillow
pyinstaller build_neroai.spec
```

The `.exe` will be in the `dist/` folder.

**Via GitHub Actions (build from Mac/Linux):**

Create `.github/workflows/build.yml`:
```yaml
name: Build Windows EXE

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pyinstaller ib_insync requests pillow
      - run: pyinstaller build_neroai.spec
      - uses: actions/upload-artifact@v3
        with:
          name: NeroAI_CopyTrade
          path: dist/NeroAI_CopyTrade.exe
```

Push to `main` → go to **Actions** tab → download the `.exe` artifact.

---

## Requirements

```
ib_insync
requests
flask
pillow
```

---

## Configuration

| Variable | File | Default | Description |
|----------|------|---------|-------------|
| `VPS_URL` | `fetch_orders.py` | `http://YOUR_VPS_IP:5000/order` | Your VPS address |
| `VPS_URL` | `neroai_client.py` | `http://YOUR_VPS_IP:5000/orders` | Your VPS address |
| TWS Host | GUI / `fetch_orders.py` | `127.0.0.1` | TWS host |
| TWS Port | GUI / `fetch_orders.py` | `7496` | TWS port (7496=live, 7497=paper) |
| Client ID | GUI / `fetch_orders.py` | `0` / `20` | Must be unique per connection |

> ⚠️ Master machine uses `clientId=0` to see all manually placed orders. Each client must use a **different** clientId.

---

## Supported Order Types

| Type | Supported |
|------|-----------|
| Market (MKT) | ✅ |
| Limit (LMT) | ✅ |
| Stocks | ✅ |

---

## Notes

- The VPS stores orders **in memory** — they reset if the server restarts. For persistence, replace the `orders = []` list with a database (SQLite, Redis, etc.)
- Paper trading port is `7497`, live trading is `7496`
- The client deduplicates orders using `symbol + action + quantity + price` as a key — restarting the client won't re-place orders already placed in that session

---

## License

MIT © [NeroAI](https://github.com/NadirAliOfficial)