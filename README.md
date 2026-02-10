# IBKR Trade Copier

Automatically copies trades from one IBKR account to another in real-time.

## Quick Start

### 1. Install
```bash
pip install ib_insync
```

### 2. Setup TWS/Gateway

**MacBook (Source Account):**
- Open TWS → File → Global Configuration → API → Settings
- ✅ Enable ActiveX and Socket Clients
- ❌ Read-Only API (uncheck)
- Socket port: `7496`
- Trusted IPs: `127.0.0.1`
- Click OK and restart TWS

**Windows (Destination Account):**
- Open TWS → File → Global Configuration → API → Settings
- ✅ Enable ActiveX and Socket Clients
- ❌ Read-Only API (uncheck)
- ❌ Allow connections from localhost only (uncheck)
- Socket port: `7497`
- Trusted IPs: `10.53.109.84` (your MacBook's IP)
- Click OK and restart TWS

**Firewall (Windows):**
```powershell
New-NetFirewallRule -DisplayName "IBKR API" -Direction Inbound -LocalPort 7497 -Protocol TCP -Action Allow
```

### 3. Run
```bash
python ibkr_trade_copier_polling.py
```

## How It Works

- Checks for new trades every 2 seconds
- Copies ALL existing trades on startup
- Automatically places same orders in destination account
- Uses market orders for instant execution

## Configuration

Edit these lines in the script:
```python
SOURCE_HOST = '127.0.0.1'      # MacBook (local)
SOURCE_PORT = 7496              # Source TWS port
DEST_HOST = '10.53.109.247'    # Windows PC IP
DEST_PORT = 7497                # Destination TWS port
POLL_INTERVAL = 2               # Check every 2 seconds
```

## Important

⚠️ **Test with paper trading first!**
⚠️ Ensure destination account has sufficient buying power
⚠️ Both accounts must be able to trade the same symbols
⚠️ Script runs on MacBook and connects to both PCs

## Troubleshooting

**Can't connect to source:**
- Is TWS running on MacBook?
- Is API enabled with port 7496?

**Can't connect to destination:**
- Is TWS running on Windows?
- Did you add MacBook IP (10.53.109.84) to Windows TWS Trusted IPs?
- Is firewall rule added?
- Test: `nc -zv 10.53.109.247 7497` (should succeed)

**Trades not copying:**
- Check console for errors
- Verify destination account has buying power
- Make sure orders are actually executing (filled status)