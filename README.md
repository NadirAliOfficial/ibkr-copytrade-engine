# ⬡ Pax Americana

> Mirror trades from a master IBKR account to unlimited client accounts in real-time.

![Pax Americana](https://img.shields.io/badge/Pax%20Americana-Engine-00d4aa?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge)
![IBKR](https://img.shields.io/badge/Interactive%20Brokers-TWS-red?style=for-the-badge)

---

## How It Works

```
Master Machine (Windows RDP / VPS with TWS)
        │
        ├── master.py
        │     ├── Connects to TWS (clientId=0 — sees ALL manual orders)
        │     ├── Captures orders in real-time
        │     ├── Serves orders + master balance via Flask API (:5000)
        │     └── Auto-updates master balance every 30 seconds
        │
        │  HTTP GET (poll every 2 seconds)
        ▼
Client Machine (Any Windows Machine)
        │
        └── Pax_Americana.exe
              ├── Connects to client's own TWS
              ├── Polls master API for new orders
              ├── Applies proportional sizing + multiplier
              └── Places orders in client IBKR account
```

---

## Project Structure

```
ibkr-copytrade-engine/
├── master.py             # Runs on master Windows machine — TWS + Flask in one
├── NeroAI_CopyTrade.py   # Client GUI app — polls master & places orders
├── build_neroai.spec     # PyInstaller spec to build Windows .exe
├── neroai.ico            # App icon (embedded in .exe)
├── requirements.txt      # Python dependencies
├── README.md
└── .github/
    └── workflows/
        └── build.yml     # Auto-builds Windows .exe on push to main
```

---

## Setup

### 1. Master Machine (Windows RDP / VPS)

The master machine runs TWS 24/7 and serves orders to all clients.

**Requirements:**
- TWS (Trader Workstation) running and logged in
- API enabled in TWS: `Edit → Global Config → API → Enable ActiveX and Socket Clients`
- Port 5000 open in Windows Firewall

**Open firewall (run as Administrator in CMD):**
```bash
netsh advfirewall firewall add rule name="PaxAmericana" dir=in action=allow protocol=TCP localport=5000
```

**Install:**
```bash
pip install ib_insync flask
```

**Run:**
```bash
python master.py
```

`master.py` will:
- Connect to TWS on `127.0.0.1:7496`
- Capture all open and new orders in real-time
- Start Flask API on port `5000`
- Serve orders + master balance to all clients

**API Endpoints:**
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/orders?since=N` | Returns new orders from index N |
| GET | `/balance` | Returns master account balance |
| GET | `/status` | Server status + total orders |
| POST | `/clear` | Clear order list |

---

### 2. Client Machine (Windows)

Each client runs `Pax_Americana.exe` on their own machine with their own TWS.

**Requirements:**
- TWS installed, running, and logged in to their IBKR account
- API enabled in TWS settings

**Configuration (inside `NeroAI_CopyTrade.py` before building .exe):**
```python
MASTER_URL = "http://YOUR_MASTER_IP:5000"
```
Replace `YOUR_MASTER_IP` with the public IP of the master Windows machine.
Find it at: https://whatismyip.com (run on master machine)

---

## Client Features

### TWS Connection
- **Live** → auto-connects to port `7496`
- **Paper** → auto-connects to port `7497`
- No manual port or host entry needed

### Copy Mode
| Mode | Description |
|------|-------------|
| New Trades Only | Only mirrors orders placed after pressing START |
| Existing + New Trades | Mirrors all current open orders + new orders |

### Trading Mode
| Mode | Description |
|------|-------------|
| Long & Short | Mirrors both BUY and SELL orders |
| Long Only | Only mirrors BUY orders — SELL orders are skipped |

### Risk Management
| Setting | Range | Description |
|---------|-------|-------------|
| Size Multiplier | 0.1x to 5.0x | Scales order quantity proportionally |
| Max Drawdown | 1% to 50% | Stops copying if client balance drops by this % |

**Proportional Sizing Formula:**
```
client_qty = master_qty x (client_balance / master_balance) x multiplier

Example:
  Master balance  = $25,000
  Client balance  = $100,000
  Master places   = BUY 100 TSLA
  Multiplier      = 1.0

  Ratio           = 100,000 / 25,000 = 4.0
  Client qty      = 100 x 4.0 x 1.0 = 400 shares
```

---

## Building the Windows .exe

### Via GitHub Actions (recommended)

Push to `main` — GitHub Actions automatically builds the `.exe`.
Go to **Actions** tab → download `Pax_Americana_EXE` artifact.

The app icon is automatically extracted and embedded into the `.exe` during build.

### Manually on Windows

```bash
pip install pyinstaller ib_insync requests pillow tzdata
pyinstaller build_neroai.spec
```

The `.exe` will be in the `dist/` folder.

---

## Requirements

```
ib_insync
requests
flask
pillow
tzdata
```

---

## Supported Order Types

| Type | Supported |
|------|-----------|
| Market (MKT) | Yes |
| Limit (LMT) | Yes |
| Stocks | Yes |
| BUY | Yes |
| SELL | Yes (skipped in Long Only mode) |

---

## Deployment Checklist

**Master Machine:**
- [ ] TWS running and logged in
- [ ] API enabled in TWS settings
- [ ] Port 5000 open in Windows Firewall
- [ ] `master.py` running
- [ ] Test: `curl http://YOUR_IP:5000/status`

**Client Machine:**
- [ ] TWS running and logged in
- [ ] API enabled in TWS settings
- [ ] `MASTER_URL` set to master machine IP
- [ ] `.exe` built and distributed to client
- [ ] Select Live or Paper mode
- [ ] Set multiplier and max drawdown
- [ ] Press START

---

## Notes

- `master.py` uses `clientId=0` to capture ALL manually placed orders in TWS
- Orders are stored in memory — reset if `master.py` restarts
- Each client connects to their own TWS with their own account
- Max drawdown is measured from the balance at the time START is pressed
- When max drawdown is hit, copying stops — client presses START again to resume

---

## Credits

Built by **Nadir Ali Khan** — [theteamnak.com](https://theteamnak.com)

© Pax Americana | [github.com/NadirAliOfficial](https://github.com/NadirAliOfficial)
<!-- updated: 2026-04-04-04 -->
