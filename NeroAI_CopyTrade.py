import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import sys
import threading, requests, time, io, base64
from datetime import datetime
from PIL import Image, ImageTk
from ib_insync import IB, Stock, MarketOrder, LimitOrder

def _resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, rel_path)

def _remove_near_black_bg(img: Image.Image, threshold: int = 18) -> Image.Image:
    rgba = img.convert("RGBA")
    new_px = []
    for (r, g, b, a) in rgba.getdata():
        if r < threshold and g < threshold and b < threshold:
            new_px.append((r, g, b, 0))
        else:
            new_px.append((r, g, b, a))
    rgba.putdata(new_px)
    return rgba

def _pad_to_square(img: Image.Image, pad_ratio: float = 0.10) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    side = max(w, h)
    pad = int(side * pad_ratio)
    side2 = side + pad * 2
    canvas = Image.new("RGBA", (side2, side2), (0, 0, 0, 0))
    canvas.paste(rgba, ((side2 - w) // 2, (side2 - h) // 2), rgba)
    return canvas

def _trim_transparent(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    bbox = rgba.split()[-1].getbbox()
    return rgba.crop(bbox) if bbox else rgba

# ── config ────────────────────────────────────────────────────────────────────
MASTER_URL        = "http://170.39.187.228:5001"
SYNC_INTERVAL_SEC = 15   # position sync check every 15 seconds

# ── theme ─────────────────────────────────────────────────────────────────────
BG     = "#0d1526"
PANEL  = "#111d35"
PANEL2 = "#0f1a2e"
BORDER = "#1a2a45"
TEAL   = "#00d4aa"
CYAN   = "#00c8ff"
GREEN  = "#00ff99"
RED    = "#ff4060"
YELLOW = "#ffd166"
TEXT   = "#e8f0ff"
SUB    = "#4a6080"
WHITE  = "#ffffff"
DIM2   = "#2a3a55"

LOGO_B64 = ""
ICON_B64 = ""


class PaxAmericanaClient:
    def __init__(self, root):
        self.root    = root
        self.root.title("Pax Americana")
        self.root.geometry("1000x750")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.ib                    = IB()
        self.running               = False
        self._last_idx             = 0
        self._stop                 = threading.Event()
        self._counts               = {"received": 0, "placed": 0, "failed": 0}
        self._mode                 = tk.StringVar(value="new")
        self._trade_mode           = tk.StringVar(value="long_short")
        self._account_mode         = tk.StringVar(value="live")
        self._multiplier           = tk.DoubleVar(value=1.0)
        self._max_drawdown         = tk.DoubleVar(value=10.0)
        self._start_balance        = 0.0
        self._master_balance       = 0.0
        self._drawdown_hit         = False
        self._last_poll_warn       = 0.0
        self._last_idx_needs_reset = True
        self._last_sync_time       = 0.0
        self._sync_done_close      = set()
        self._sync_done_open       = set()
        self._positions_cache      = {}      # symbol -> {position, contract} — updated by background thread
        self._positions_cache_lock = threading.Lock()
        self._close_all_done       = set()   # symbols already submitted via Close All this session
        self._close_all_running    = False   # prevent concurrent Close All threads

        self._build_ui()
        self._set_icon()

    # ── icon ──────────────────────────────────────────────────────────────────
    def _set_icon(self):
        try:
            icon_path = _resource_path(os.path.join("assets", "pax_americana.png"))
            pil_icon = Image.open(icon_path)
            pil_icon = _remove_near_black_bg(pil_icon)
            pil_icon = _trim_transparent(pil_icon)
            pil_icon = _pad_to_square(pil_icon, pad_ratio=0.04)
            self._app_icon_imgs = []
            for s in [512, 256, 128, 64, 32, 16]:
                im = pil_icon.resize((s, s), Image.LANCZOS)
                self._app_icon_imgs.append(ImageTk.PhotoImage(im))
            self.root.iconphoto(True, *self._app_icon_imgs)
            return
        except Exception:
            pass
        try:
            if ICON_B64:
                import tempfile
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ico")
                tmp.write(base64.b64decode(ICON_B64))
                tmp.close()
                self.root.iconbitmap(tmp.name)
        except Exception:
            pass

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=PANEL2)
        hdr.pack(fill="x")
        stripe = tk.Canvas(hdr, height=3, bg=BG, highlightthickness=0)
        stripe.pack(fill="x")
        for i in range(1000):
            g = int(0xd4 + (0xc8 - 0xd4) * i / 1000)
            b = int(0xaa + (0xff - 0xaa) * i / 1000)
            stripe.create_line(i, 0, i, 3, fill=f"#00{g:02x}{b:02x}")
        inner = tk.Frame(hdr, bg=PANEL2, padx=20, pady=12)
        inner.pack(fill="x")

        try:
            if LOGO_B64:
                pil_img = Image.open(io.BytesIO(base64.b64decode(LOGO_B64))).convert("RGBA")
                try:
                    bg_pixel = pil_img.getpixel((0, 0))[:3]
                    tol = 28
                    new_px = [(r, g, b, 0) if abs(r-bg_pixel[0])<=tol and abs(g-bg_pixel[1])<=tol and abs(b-bg_pixel[2])<=tol else (r, g, b, a)
                              for (r, g, b, a) in pil_img.getdata()]
                    pil_img.putdata(new_px)
                except Exception:
                    pass
                self._logo_img = ImageTk.PhotoImage(pil_img)
                tk.Label(inner, image=self._logo_img, bg=PANEL2, bd=0).pack(side="left")
        except Exception:
            pass

        tk.Label(inner, text="  Pax Americana",
                 font=("Segoe UI", 10), fg=SUB, bg=PANEL2).pack(side="left")
        self._time_lbl = tk.Label(inner, text="", font=("Courier New", 10), fg=SUB, bg=PANEL2)
        self._time_lbl.pack(side="right")
        self._tick_clock()
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # status bar
        sbar = tk.Frame(self.root, bg=BG, padx=24, pady=10)
        sbar.pack(fill="x")
        self._dot = tk.Label(sbar, text="●", font=("Segoe UI", 13), fg=RED, bg=BG)
        self._dot.pack(side="left")
        self._status_lbl = tk.Label(sbar, text="  Disconnected",
                                     font=("Segoe UI", 10, "bold"), fg=RED, bg=BG)
        self._status_lbl.pack(side="left")
        self._bal_lbl = tk.Label(sbar, text="Net Liquidation:  —",
                                  font=("Segoe UI", 10), fg=SUB, bg=BG)
        self._bal_lbl.pack(side="right")

        # connection panel
        cp = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        cp.pack(fill="x", padx=24, pady=(4, 8))
        ci = tk.Frame(cp, bg=PANEL, padx=20, pady=10)
        ci.pack(fill="x")
        tk.Label(ci, text="TWS CONNECTION", font=("Segoe UI", 8, "bold"),
                 fg=TEAL, bg=PANEL).grid(row=0, column=0, columnspan=8, sticky="w", pady=(0,8))

        tk.Label(ci, text="Mode", font=("Segoe UI", 10), fg=SUB, bg=PANEL).grid(
            row=1, column=0, sticky="w", padx=(0,4))
        acct_frame = tk.Frame(ci, bg=PANEL)
        acct_frame.grid(row=2, column=0, padx=(0,20))
        for val, lbl in [("live","Live"), ("paper","Paper")]:
            tk.Radiobutton(
                acct_frame, text=lbl, variable=self._account_mode, value=val,
                font=("Segoe UI", 10), fg=TEXT, bg=PANEL,
                selectcolor=DIM2, activebackground=PANEL, activeforeground=TEAL,
                indicatoron=0, relief="flat", cursor="hand2",
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=TEAL, padx=12, pady=5,
                command=self._on_account_mode_change
            ).pack(side="left", padx=(0,4))

        self._btn = tk.Button(ci, text="▶   START", font=("Segoe UI", 11, "bold"),
                               bg=TEAL, fg="#0a1220", relief="flat",
                               activebackground="#00e8c0", activeforeground="#0a1220",
                               cursor="hand2", padx=28, pady=9, command=self._toggle)
        self._btn.grid(row=2, column=1)

        self._close_all_btn = tk.Button(
            ci, text="CLOSE ALL TRADES", font=("Segoe UI", 11, "bold"),
            bg=YELLOW, fg="#0a1220", relief="flat",
            activebackground="#ffe08a", activeforeground="#0a1220",
            cursor="hand2", padx=22, pady=9, command=self._close_all_trades
        )
        self._close_all_btn.grid(row=2, column=2, padx=(10, 0))

        self._add_toggle_panel("EXECUTION MODE", self._mode,
            [("new","New Trades Only"),("all","Existing + New Trades")],
            "_mode_lbl", self._on_mode_change)

        self._add_toggle_panel("TRADING MODE", self._trade_mode,
            [("long_short","Long & Short"),("long_only","Long Only")],
            "_trade_lbl", self._on_trade_mode_change)

        # risk management
        rm = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        rm.pack(fill="x", padx=24, pady=(0, 8))
        rm_inner = tk.Frame(rm, bg=PANEL, padx=20, pady=10)
        rm_inner.pack(fill="x")
        tk.Label(rm_inner, text="RISK MANAGEMENT", font=("Segoe UI", 8, "bold"),
                 fg=TEAL, bg=PANEL).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0,10))

        tk.Label(rm_inner, text="Size Multiplier", font=("Segoe UI", 10), fg=SUB, bg=PANEL).grid(
            row=1, column=0, sticky="w", padx=(0,10))
        self._mult_val_lbl = tk.Label(rm_inner, text="1.0×",
                                       font=("Segoe UI", 10, "bold"), fg=TEAL, bg=PANEL, width=5)
        self._mult_val_lbl.grid(row=1, column=1, padx=(0,10))
        tk.Scale(rm_inner, from_=0.1, to=5.0, resolution=0.1, orient="horizontal",
                 variable=self._multiplier, bg=PANEL, fg=TEXT, troughcolor=DIM2,
                 highlightthickness=0, relief="flat", activebackground=TEAL,
                 sliderrelief="flat", length=200, showvalue=0,
                 command=self._on_mult_change).grid(row=1, column=2, padx=(0,40))
        tk.Label(rm_inner, text="0.1×", font=("Segoe UI", 7), fg=SUB, bg=PANEL).grid(row=2, column=2, sticky="w")
        tk.Label(rm_inner, text="5.0×", font=("Segoe UI", 7), fg=SUB, bg=PANEL).grid(row=2, column=2, sticky="e", padx=(0,40))

        tk.Label(rm_inner, text="Max Drawdown", font=("Segoe UI", 10), fg=SUB, bg=PANEL).grid(
            row=1, column=3, sticky="w", padx=(0,10))
        self._dd_val_lbl = tk.Label(rm_inner, text="10.0%",
                                     font=("Segoe UI", 10, "bold"), fg=RED, bg=PANEL, width=6)
        self._dd_val_lbl.grid(row=1, column=4, padx=(0,10))
        tk.Scale(rm_inner, from_=1.0, to=50.0, resolution=0.5, orient="horizontal",
                 variable=self._max_drawdown, bg=PANEL, fg=TEXT, troughcolor=DIM2,
                 highlightthickness=0, relief="flat", activebackground=RED,
                 sliderrelief="flat", length=200, showvalue=0,
                 command=self._on_dd_change).grid(row=1, column=5, padx=(0,10))
        tk.Label(rm_inner, text="1%",  font=("Segoe UI", 7), fg=SUB, bg=PANEL).grid(row=2, column=5, sticky="w")
        tk.Label(rm_inner, text="50%", font=("Segoe UI", 7), fg=SUB, bg=PANEL).grid(row=2, column=5, sticky="e", padx=(0,10))

        self._risk_lbl = tk.Label(rm_inner,
            text="Proportional sizing active. Trading stops if drawdown exceeds 10.0%",
            font=("Segoe UI", 10), fg=SUB, bg=PANEL)
        self._risk_lbl.grid(row=3, column=0, columnspan=6, sticky="w", pady=(8,0))

        # stat cards
        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=24, pady=(0, 8))
        self._stat_labels = {}
        for i, (title, key, color) in enumerate([
                ("ORDERS RECEIVED","received",CYAN),
                ("ORDERS PLACED","placed",TEAL),
                ("FAILED","failed",RED)]):
            f = tk.Frame(cards, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            f.pack(side="left", fill="x", expand=True, padx=(0 if i==0 else 8, 0))
            tk.Label(f, text=title, font=("Segoe UI", 8, "bold"), fg=SUB, bg=PANEL).pack(pady=(10,0))
            v = tk.Label(f, text="0", font=("Courier New", 22, "bold"), fg=color, bg=PANEL)
            v.pack(pady=(2,10))
            self._stat_labels[key] = v

        # log
        lf = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        lf.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        lf_hdr = tk.Frame(lf, bg=BORDER, padx=16, pady=6)
        lf_hdr.pack(fill="x")
        tk.Label(lf_hdr, text="LIVE ORDER FEED",
                 font=("Segoe UI", 10, "bold"), fg=TEAL, bg=BORDER).pack(side="left")
        actions = tk.Frame(lf_hdr, bg=BORDER)
        actions.pack(side="right")
        ca_lbl = tk.Label(actions, text="CLOSE ALL TRADES",
                          font=("Segoe UI", 10, "bold"), fg=YELLOW, bg=BORDER, cursor="hand2")
        ca_lbl.pack(side="right", padx=(12, 0))
        ca_lbl.bind("<Button-1>", lambda e: self._close_all_trades())
        clr = tk.Label(actions, text="clear", font=("Segoe UI", 10), fg=SUB, bg=BORDER, cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda e: self._clear_log())

        self.log = scrolledtext.ScrolledText(
            lf, font=("Consolas", 10), bg="#080e1a", fg=TEXT,
            insertbackground=TEAL, relief="flat", bd=0,
            state="disabled", wrap="none", padx=14, pady=10)
        self.log.pack(fill="both", expand=True)

        for tag, color in [("ok",GREEN),("err",RED),("info",CYAN),("warn",YELLOW),
                           ("dim",SUB),("buy","#00ff99"),("sell","#ff4060"),
                           ("symbol",WHITE),("price",CYAN)]:
            self.log.tag_config(tag, foreground=color)

        self._log_info("Pax Americana ready. Configure connection and press START.")

    def _add_toggle_panel(self, label, var, options, desc_var, callback):
        f = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill="x", padx=24, pady=(0, 8))
        inner = tk.Frame(f, bg=PANEL, padx=20, pady=12)
        inner.pack(fill="x")
        tk.Label(inner, text=label, font=("Segoe UI", 8, "bold"),
                 fg=TEAL, bg=PANEL).pack(side="left", padx=(0,20))
        for val, lbl in options:
            tk.Radiobutton(
                inner, text=lbl, variable=var, value=val,
                font=("Segoe UI", 10), fg=TEXT, bg=PANEL,
                selectcolor=DIM2, activebackground=PANEL, activeforeground=TEAL,
                indicatoron=0, relief="flat", cursor="hand2",
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=TEAL, padx=14, pady=6, command=callback
            ).pack(side="left", padx=(0,8))
        lbl_w = tk.Label(inner, text="", font=("Segoe UI", 10), fg=SUB, bg=PANEL)
        lbl_w.pack(side="left", padx=(10,0))
        setattr(self, desc_var, lbl_w)
        callback()

    # ── callbacks ─────────────────────────────────────────────────────────────
    def _on_account_mode_change(self): pass

    def _on_mode_change(self):
        self._mode_lbl.config(text="Only new orders placed after START will be executed"
            if self._mode.get() == "new" else "All current open orders + new orders will be executed")

    def _on_trade_mode_change(self):
        self._trade_lbl.config(text="SELL orders will be skipped"
            if self._trade_mode.get() == "long_only" else "BUY and SELL orders will be executed")

    def _on_mult_change(self, val):
        self._mult_val_lbl.config(text=f"{float(val):.1f}×")
        self._update_risk_lbl()

    def _on_dd_change(self, val):
        self._dd_val_lbl.config(text=f"{float(val):.1f}%")
        self._update_risk_lbl()

    def _update_risk_lbl(self):
        self._risk_lbl.config(
            text=f"Proportional sizing × {self._multiplier.get():.1f}. "
                 f"Trading stops if drawdown exceeds {self._max_drawdown.get():.1f}%")

    def _tick_clock(self):
        self._time_lbl.config(text=datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ── logging ───────────────────────────────────────────────────────────────
    def _log_raw(self, parts):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}]  ", "dim")
        for text, tag in parts:
            self.log.insert("end", text, tag)
        self.log.insert("end", "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _log_info(self, msg):  self._log_raw([(msg, "info")])
    def _log_err(self, msg):   self._log_raw([(msg, "err")])
    def _log_warn(self, msg):  self._log_raw([(msg, "warn")])
    def _log_ok(self, msg):    self._log_raw([(msg, "ok")])

    def _log_order(self, o, qty):
        tag = "buy" if o["action"] == "BUY" else "sell"
        self._log_raw([
            (f"{o['action']:<4s}  ", tag),
            (f"{o['symbol']:<6s}", "symbol"),
            (f"  qty={qty}  {o['orderType']} @ ", "dim"),
            (f"{o['price']}", "price"),
        ])

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _set_status(self, connected):
        c = GREEN if connected else RED
        self._dot.config(fg=c)
        self._status_lbl.config(
            text="  Connected  —  Scanning active" if connected else "  Disconnected", fg=c)

    def _inc(self, key):
        self._counts[key] += 1
        self._stat_labels[key].config(text=str(self._counts[key]))

    # ── close all trades ──────────────────────────────────────────────────────
    def _close_all_trades(self):
        if not self.running:
            self._log_warn("Not connected — press START first.")
            return
        if not messagebox.askyesno(
            "Close All Trades",
            "This will CANCEL all open orders and CLOSE ALL open positions\n"
            "using MARKET orders.\n\nAre you sure?"
        ):
            return
        threading.Thread(target=self._close_all_worker, daemon=True).start()

    def _close_all_worker(self):
        if self._close_all_running:
            self.root.after(0, lambda: self._log_warn("Close all already running — please wait."))
            return
        self._close_all_running = True
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        try:
            # Step 1: cancel any pending open orders (don't use reqAllOpenOrders — it hangs)
            self.root.after(0, lambda: self._log_warn("Close all: cancelling pending orders…"))
            cancelled = 0
            try:
                for t in list(self.ib.trades()):
                    st = t.orderStatus.status
                    if st in ("Submitted", "PreSubmitted", "PendingSubmit", "PendingCancel"):
                        try:
                            self.ib.cancelOrder(t.order)
                            cancelled += 1
                        except Exception:
                            pass
                time.sleep(0.8)
            except Exception:
                pass
            self.root.after(0, lambda c=cancelled: self._log_info(f"Cancelled {c} pending orders."))

            # Step 2: read from positions cache — populated by main run loop
            self.root.after(0, lambda: self._log_warn("Close all: reading positions…"))
            with self._positions_cache_lock:
                snapshot = dict(self._positions_cache)

            # Filter out symbols already submitted this session
            pending = {s: d for s, d in snapshot.items() if s not in self._close_all_done}

            if not pending:
                self.root.after(0, lambda: self._log_ok("No new positions to close — orders already submitted."))
                return

            self.root.after(0, lambda n=len(pending): self._log_warn(f"Closing {n} positions…"))

            # Step 3: place closing market orders
            closed = 0
            for sym, cdata in pending.items():
                try:
                    qty     = float(cdata["position"])
                    abs_qty = int(abs(qty))
                    if abs_qty == 0:
                        continue
                    action   = "SELL" if qty > 0 else "BUY"
                    contract = cdata["contract"]
                    currency = contract.currency or "USD"

                    c         = Stock(symbol=sym, exchange="SMART", currency=currency)
                    c.conId   = contract.conId
                    order     = MarketOrder(action, abs_qty)
                    order.tif = "DAY"

                    self.ib.placeOrder(c, order)
                    self._close_all_done.add(sym)  # never re-submit this symbol
                    closed += 1
                    self.root.after(0, lambda s=sym, a=action, q=abs_qty:
                        self._log_ok(f"Close all: {a} {s}  qty={q}  MKT ✓"))
                    time.sleep(0.3)
                except Exception as e:
                    sym2 = sym
                    self.root.after(0, lambda s=sym2, e=e:
                        self._log_err(f"Close all failed {s}: {e}"))

            self.root.after(0, lambda c=closed: self._log_ok(f"Done — submitted {c} closing orders."))

        except Exception as e:
            self.root.after(0, lambda e=e: self._log_err(f"Close all error: {e}"))
        finally:
            self._close_all_running = False

    # ── position sync ─────────────────────────────────────────────────────────
    def _refresh_positions_cache(self):
        """
        Refreshes _positions_cache from ib.portfolio() (incremental updates).
        Called every 2s from the main run loop.
        """
        try:
            snapshot = {}
            for item in self.ib.portfolio():
                qty = float(item.position)
                if qty == 0:
                    continue
                snapshot[item.contract.symbol] = {
                    "position": qty,
                    "contract": item.contract,
                }
            with self._positions_cache_lock:
                self._positions_cache.clear()
                self._positions_cache.update(snapshot)
        except Exception:
            pass

    def _force_refresh_positions_cache(self):
        """
        Forces a FULL position refresh using reqPositions() — use for initial sync only.
        reqPositions() must be called from the IB event loop thread (main _run thread).
        Returns the snapshot dict for immediate use.
        """
        try:
            self.ib.reqPositions()
            # Wait for TWS to stream all positions — poll until stable
            prev_count = -1
            stable_checks = 0
            for _ in range(20):  # max 10 seconds
                time.sleep(0.5)
                positions = self.ib.positions()
                curr_count = len([p for p in positions if float(p.position) != 0])
                if curr_count == prev_count:
                    stable_checks += 1
                    if stable_checks >= 3:  # stable for 1.5s — done
                        break
                else:
                    stable_checks = 0
                prev_count = curr_count

            snapshot = {}
            for p in self.ib.positions():
                qty = float(p.position)
                if qty == 0:
                    continue
                snapshot[p.contract.symbol] = {
                    "position": qty,
                    "contract": p.contract,
                }
            with self._positions_cache_lock:
                self._positions_cache.clear()
                self._positions_cache.update(snapshot)
            return snapshot
        except Exception as e:
            return {}

    def _sync_positions(self):
        """
        Every SYNC_INTERVAL_SEC seconds, compare master positions vs client positions.

        Case 1: Master HAS symbol, Client DOES NOT  → open it on client (once per session)
        Case 2: Client HAS symbol, Master DOES NOT  → close it on client (once per session)

        _sync_done_close / _sync_done_open are session-scoped sets.
        Once an order is submitted for a symbol, we NEVER resubmit it this session.
        User must press STOP then START to reset.
        """
        # Fetch master positions
        try:
            base_url = MASTER_URL.rstrip("/")
            resp = requests.get(f"{base_url}/positions", timeout=6).json()
            master_positions = resp.get("positions", [])
            # Safety guard: if master returns an error or empty list, it may not be
            # properly connected. Never close client positions based on an empty response —
            # that would wipe out all positions incorrectly.
            if resp.get("error"):
                self.root.after(0, lambda: self._log_warn("Sync skipped — master not connected."))
                return
        except Exception:
            return  # network issue — retry next cycle silently

        master_map = {p["symbol"]: p for p in master_positions}

        # Read from our own positions cache — populated by main run loop
        with self._positions_cache_lock:
            client_map = dict(self._positions_cache)

        # Safety guard: if master has 0 positions AND client has many,
        # this is almost certainly a connectivity/startup issue on the master side.
        # Never close all client positions based on this — skip sync.
        if len(master_map) == 0 and len(client_map) > 2:
            self.root.after(0, lambda: self._log_warn(
                "Sync skipped — master shows 0 positions but client has open trades. "
                "Check master connection."
            ))
            return

        # ── Case 1: Master has it, client doesn't → open on client ───────────
        for sym, mp in master_map.items():
            if sym in client_map:
                # Symbol now in client — remove from done so future sessions re-check
                self._sync_done_open.discard(sym)
                continue
            if sym in self._sync_done_open:
                continue  # already submitted this session — don't repeat
            qty = self._calc_quantity(mp["quantity"])
            if qty <= 0:
                continue
            action   = mp["side"]
            currency = mp.get("currency", "USD")
            if self._trade_mode.get() == "long_only" and action == "SELL":
                continue
            try:
                contract  = Stock(symbol=sym, exchange="SMART", currency=currency)
                order     = MarketOrder(action, qty)
                order.tif = "DAY"
                self.ib.placeOrder(contract, order)
                self._sync_done_open.add(sym)
                self.root.after(0, lambda s=sym, a=action, q=qty:
                    self._log_warn(f"Sync: opening missed position — {a} {s} qty={q}"))
                time.sleep(0.5)  # small gap between orders to avoid TWS rate limit
            except Exception as e:
                self.root.after(0, lambda s=sym, e=e:
                    self._log_err(f"Sync open failed {s}: {e}"))

        # ── Case 2: Client has it, master doesn't → close on client ──────────
        for sym, cdata in client_map.items():
            if sym in master_map:
                self._sync_done_close.discard(sym)  # master has it again — reset
                continue
            if sym in self._sync_done_close:
                continue  # already submitted this session — don't repeat
            qty     = float(cdata["position"])
            abs_qty = int(abs(qty))
            if abs_qty == 0:
                continue
            action   = "SELL" if qty > 0 else "BUY"
            contract = cdata["contract"]
            currency = contract.currency or "USD"
            try:
                c       = Stock(symbol=sym, exchange="SMART", currency=currency)
                c.conId = contract.conId
                order   = MarketOrder(action, abs_qty)
                order.tif = "DAY"
                self.ib.placeOrder(c, order)
                self._sync_done_close.add(sym)
                self.root.after(0, lambda s=sym, a=action, q=abs_qty:
                    self._log_warn(f"Sync: closing orphan position — {a} {s} qty={q}"))
                time.sleep(0.3)
            except Exception as e:
                self.root.after(0, lambda s=sym, e=e:
                    self._log_err(f"Sync close failed {s}: {e}"))

    # ── start / stop ──────────────────────────────────────────────────────────
    def _toggle(self):
        if not self.running: self._start()
        else: self._stop_engine()

    def _start(self):
        host = "127.0.0.1"
        port = 7496 if self._account_mode.get() == "live" else 7497
        cid  = 20
        self._btn.config(text="■   STOP", bg=RED, activebackground="#cc2244", fg="#0a1220")
        self._log_info(f"Connecting to TWS  {host}:{port}  clientId={cid} …")
        self._drawdown_hit         = False
        self._last_sync_time       = time.time() + 9999  # block periodic sync until startup sync completes
        self._sync_done_close      = set()
        self._sync_done_open       = set()
        with self._positions_cache_lock:
            self._positions_cache.clear()
        self._close_all_done = set()
        threading.Thread(target=self._run, args=(host, port, cid), daemon=True).start()

    def _stop_engine(self):
        self._stop.set()
        self.running = False
        self._last_idx_needs_reset = True
        self._btn.config(text="▶   START", bg=TEAL, activebackground="#00e8c0", fg="#0a1220")
        self.root.after(0, lambda: self._set_status(False))
        self._log_warn("Engine stopped.")
        try: self.ib.disconnect()
        except: pass
        self.ib = IB()

    # ── main loop ─────────────────────────────────────────────────────────────
    def _run(self, host, port, cid):
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._stop.clear()

        try:
            self.ib.connect(host, port, clientId=cid)
            self.running = True
            self.root.after(0, lambda: self._set_status(True))
            self._log_info("TWS connected ✓")
            self._log_info(f"Mode: {self._mode.get()} | Account: {self._account_mode.get()}")
            self._fetch_client_balance()
        except Exception:
            self.root.after(0, lambda: self._log_err(
                "Connection failed. Make sure TWS is running and API is enabled."))
            self.root.after(0, lambda: self._btn.config(text="▶   START", bg=TEAL, fg="#0a1220"))
            return

        base_url = MASTER_URL.rstrip("/")

        # fetch master balance
        try:
            resp = requests.get(f"{base_url}/balance", timeout=4).json()
            self._master_balance = float(resp.get("master_balance", 0))
        except Exception:
            pass

        # determine starting order index
        # We ALWAYS start from the latest index regardless of mode.
        # Existing positions are handled by the position sync (every 15s),
        # which compares master vs client positions and only acts on mismatches.
        # This prevents double-placing orders that are already in the account.
        if getattr(self, "_last_idx_needs_reset", True):
            try:
                resp = requests.get(f"{base_url}/orders", timeout=4).json()
                self._last_idx = resp.get("total", 0)
            except Exception:
                pass
            self._last_idx_needs_reset = False

        # If "Existing + New Trades" mode — force full position load then sync
        if self._mode.get() == "all":
            self.root.after(0, lambda: self._log_info("Existing + New mode — fetching all positions…"))
            # Block periodic sync for the full duration of startup sync
            self._last_sync_time = time.time() + 9999
            # Run entirely in THIS thread — has the IB event loop for both reqPositions + placeOrder
            snapshot = self._force_refresh_positions_cache()
            n = len(snapshot)
            self.root.after(0, lambda n=n: self._log_info(f"Position cache ready — {n} positions found. Running sync…"))
            self._sync_positions()   # called directly — same thread, same event loop
            self._last_sync_time = time.time()  # periodic sync resumes from now

        while not self._stop.is_set():

            # ── drawdown guard ────────────────────────────────────────────────
            if self._drawdown_hit:
                time.sleep(2)
                continue

            current_bal = self._get_client_balance()
            if current_bal > 0 and self._start_balance > 0:
                dd = (self._start_balance - current_bal) / self._start_balance * 100
                if dd >= self._max_drawdown.get():
                    self._drawdown_hit = True
                    self.root.after(0, lambda: self._log_err(
                        "Max drawdown limit hit — trading stopped."))
                    self.root.after(0, lambda: self._set_status(False))
                    time.sleep(2)
                    continue

            # ── refresh positions cache (used by sync + close all) ────────────
            self._refresh_positions_cache()

            # ── poll new orders ───────────────────────────────────────────────
            try:
                resp = requests.get(
                    f"{base_url}/orders?since={self._last_idx}", timeout=4).json()
                new_orders = resp.get("orders", [])
                mb = float(resp.get("master_balance", 0))
                if mb > 0:
                    self._master_balance = mb
                for o in new_orders:
                    self._maybe_place(o)
                    self._last_idx += 1
            except Exception:
                now = time.time()
                if now - self._last_poll_warn > 30:
                    self._last_poll_warn = now
                    self.root.after(0, lambda: self._log_warn("Connection issue — retrying…"))

            # ── position sync every SYNC_INTERVAL_SEC ────────────────────────
            now = time.time()
            if now - self._last_sync_time >= SYNC_INTERVAL_SEC:
                self._last_sync_time = now
                # Run entirely in THIS thread — IB event loop required for both calls
                self._force_refresh_positions_cache()
                self._sync_positions()

            time.sleep(2)

    def _fetch_client_balance(self):
        try:
            for v in self.ib.accountValues():
                if v.tag == "NetLiquidation" and v.currency == "USD":
                    bal = float(v.value)
                    self._start_balance = bal
                    self.root.after(0, lambda b=bal: self._bal_lbl.config(
                        text=f"Net Liquidation:  ${b:,.2f}", fg=TEXT))
                    return bal
        except Exception:
            pass
        return 0.0

    def _get_client_balance(self):
        try:
            for v in self.ib.accountValues():
                if v.tag == "NetLiquidation" and v.currency == "USD":
                    bal = float(v.value)
                    self.root.after(0, lambda b=bal: self._bal_lbl.config(
                        text=f"Net Liquidation:  ${b:,.2f}", fg=TEXT))
                    return bal
        except Exception:
            pass
        return 0.0

    # ── order placement ───────────────────────────────────────────────────────
    def _maybe_place(self, o):
        if not self.running:
            return
        if self._trade_mode.get() == "long_only" and o["action"] == "SELL":
            self.root.after(0, lambda: self._log_warn(f"Skipped SELL {o['symbol']} (Long Only mode)"))
            return
        qty = self._calc_quantity(float(o["quantity"]))
        if qty <= 0:
            self.root.after(0, lambda: self._log_warn(f"Skipped {o['symbol']} — qty is 0"))
            return
        self.root.after(0, lambda: self._inc("received"))
        try:
            contract     = Stock(o["symbol"], "SMART", o["currency"])
            order        = MarketOrder(o["action"], qty) if o["orderType"] == "MKT" \
                           else LimitOrder(o["action"], qty, o["price"])
            order.tif    = "DAY"
            self.ib.placeOrder(contract, order)
            # Prevent sync from also opening/closing this symbol in the same session
            self._sync_done_open.add(o["symbol"])
            self._sync_done_close.add(o["symbol"])
            time.sleep(0.5)
            self.root.after(0, lambda: self._inc("placed"))
            self.root.after(0, lambda oo=o, q=qty: self._log_order(oo, q))
        except Exception:
            self.root.after(0, lambda: self._inc("failed"))
            self.root.after(0, lambda: self._log_err("Order failed. Check TWS for details."))

    def _calc_quantity(self, master_qty):
        multiplier = self._multiplier.get()
        if self._master_balance <= 0 or self._start_balance <= 0:
            return max(1, round(master_qty * multiplier))
        ratio = self._start_balance / self._master_balance
        return max(1, round(master_qty * ratio * multiplier))


if __name__ == "__main__":
    root = tk.Tk()
    PaxAmericanaClient(root)
    root.mainloop()