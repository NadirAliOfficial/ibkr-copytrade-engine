import tkinter as tk
from tkinter import scrolledtext
import threading, requests, time, io, base64
from datetime import datetime
from PIL import Image, ImageTk
from ib_insync import IB, Stock, MarketOrder, LimitOrder

VPS_URL = "http://187.77.200.114:5000/orders"

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

LOGO_B64 = "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"
ICON_B64 = "AAABAAQAEAQAAAAAIAA6AgAARgAAACAJAAAAACAAYwQAAIACAAAwDQAAAAAgAOsGAADjBgAAQBIAAAAAIAAkCgAAzg0AAIlQTkcNChoKAAAADUlIRFIAAAAQAAAABAgGAAAAh7S/7AAAAQhpQ0NQSUNDIFByb2ZpbGUAAHicY2BgPMEABCwGDAy5eSVFQe5OChGRUQrsDxgYgRAMEpOLCxhwA6Cqb9cgai/r4lGHC3CmpBYnA+kPQKxSBLQcaKQIkC2SDmFrgNhJELYNiF1eUlACZAeA2EUhQc5AdgqQrZGOxE5CYicXFIHU9wDZNrk5pckIdzPwpOaFBgNpDiCWYShmCGJwZ3AC+R+iJH8RA4PFVwYG5gkIsaSZDAzbWxkYJG4hxFQWMDDwtzAwbDuPEEOESUFiUSJYiAWImdLSGBg+LWdg4I1kYBC+wMDAFQ0LCBxuUwC7zZ0hHwjTGXIYUoEingx5DMkMekCWEYMBgyGDGQCm1j8/R2zgUAAAAO1JREFUeJwFwTFKw1AcwOHfey8vTdIkpbRC1ClDNi8g5BKCl3By1p5Bl25ubi4OooiDF4iLVRApWhxEzGBLBUsgafv3+1Se55KmKcu64eXtlfHkHaka6roGQGmNrNcA+L5PVVUY16KVwgt91O3NtfR7fWh7HJ2d8nlfMDge8F2WBH6A4xistUynMzzX8vUz4/zygt72FstmhR5e3XHyUTKcjHkunrArxeNoxO98TpZlGO2w+FvwUBTEcYe420XwQYco24ZgY1N2Dw5lZ29fAHFcV1peS4wxYq2VKIrFGCOAJEkigLhhLF7UEa21/AOj91ZXbkS/8wAAAABJRU5ErkJggolQTkcNChoKAAAADUlIRFIAAAAgAAAACQgGAAAAU9kuCgAAAQhpQ0NQSUNDIFByb2ZpbGUAAHicY2BgPMEABCwGDAy5eSVFQe5OChGRUQrsDxgYgRAMEpOLCxhwA6Cqb9cgai/r4lGHC3CmpBYnA+kPQKxSBLQcaKQIkC2SDmFrgNhJELYNiF1eUlACZAeA2EUhQc5AdgqQrZGOxE5CYicXFIHU9wDZNrk5pckIdzPwpOaFBgNpDiCWYShmCGJwZ3AC+R+iJH8RA4PFVwYG5gkIsaSZDAzbWxkYJG4hxFQWMDDwtzAwbDuPEEOESUFiUSJYiAWImdLSGBg+LWdg4I1kYBC+wMDAFQ0LCBxuUwC7zZ0hHwjTGXIYUoEingx5DMkMekCWEYMBgyGDGQCm1j8/R2zgUAAAAxZJREFUeJylkG9MlXUUxz+/333gGg6YQqHMEtYdJksXBk3Bxg3LeNFqq7yRvUGrTZpZgdLWWotMZ02KjdzsRXNzvahuV4GRd+jaDXwBYmvFIBdyC73YYAMSUFiD5/n2gj+b080Xne1sZ+d7znefcwwg7hLGGHw+H5IwxuC6LpJwHAcAz/MAsNYiCc/zsNZijEESrutijMEs6AbhJCcxN+tiAoGAgsEgc+4c1lrAYK1hZmqacxc7WJF9H3+c/+WOUNJd2ZfAFiEXI29rAeNDIzjl5eU0NjbetnTw44NMP5LB5R9/Jnt1Ni+GdjAxcZ2ctTkc//I4I8Mj7KnaQyAQoKGhgdS0NEqKSxgbH+N8ewelpaUUFxfzXTjMha4uMtZk82BJEWNXr3FjeJTJ4etM/3MDKndVSpLqj3yijp/aJUn79u5T2QdVyttaIECbt2yWJJ1ualIikVDk9CnV1dVp8MoVhb8P66/BQR06fEiS1N3drWNfHNPU1KTa2to0MzOj0u3bFXzzda3ZmK/8baV67siHKqx4QavzHxI1tQd0trVFDwTL9Oyu3Xrj1df01OH39H6iU/7lKTLWqrCoSNM3bwrQjlBIiWtD6r/crzPRqA7U1qqrq0uRSET9/f2y1qqvr0/19UcF6FJvr76JtSuzYP4YQI/u3KlNL1Xo3rw82W9PnuTTaDuvhFvwP/k03Q6Uvbuf35tjeLNzyPNITkrinpQU/Mv8ZGSsBEHPbz2sysoiPS2dgXiceDxOamoqnufR2dlJKBSiZn8N69av41xzM2s3FOEk+8nMDZAZ2AAmCeskY3Ofr8SuzGL80gA5j2/jmaOf8+uJMK01HzE3OwvA6OgoTS3NuK7LQDxO29k2qqqq6O3tJfhEkFORCLFYjGg0ijGG6upqWn84Q0XFy7z1Tg1fNXzG9FCC4t17uX/TY/x98QKTQ1f5d2ICcgu3CFB2/ka93fOnQie+VrJ/mQAZY5be9n9y0cdY3510ZBeEVesf1vL0FQvD9hYDn8+3VFtrl3rWWvl8vttmHGdecxznFj9jzHy9APUfoyGl4+N5WXEAAAAASUVORK5CYIKJUE5HDQoaCgAAAA1JSERSAAAAMAAAAA0IBgAAAO/m7fQAAAEIaUNDUElDQyBQcm9maWxlAAB4nGNgYDzBAAQsBgwMuXklRUHuTgoRkVEK7A8YGIEQDBKTiwsYcAOgqm/XIGov6+JRhwtwpqQWJwPpD0CsUgS0HGikCJAtkg5ha4DYSRC2DYhdXlJQAmQHgNhFIUHOQHYKkK2RjsROQmInFxSB1PcA2Ta5OaXJCHcz8KTmhQYDaQ4glmEoZghicGdwAvkfoiR/EQODxVcGBuYJCLGkmQwM21sZGCRuIcRUFjAw8LcwMGw7jxBDhElBYlEiWIgFiJnS0hgYPi1nYOCNZGAQvsDAwBUNCwgcblMAu82dIR8I0xlyGFKBIp4MeQzJDHpAlhGDAYMhgxkAptY/P0ds4FAAAAWeSURBVHicxZZ9bNXVGcc/55zb3rbUtvZdSls7oOIGgtlkTtMmyFonIGkXOggwMpoZJ8hEulli4zT7AxWGrPIyIb5sbMT9IdKuG2SuNRNjgS6lkDGsg0KR8rLbNYArF3vv/f2+++PSO8TJXpJlT3Ly+53n+T7nPOd8z3meYwA55wAwfLb4vo8MGGOQ56MbYP+XYuBTc+s/bQZkjJFzTtZaWWsVCARkrf0H5qo9EAjIWZfQj/oYYxJ4Y4wCgcCnxhi1WWdlrJExRsYa5ZYW6vNfvVuAAhkZGWzYsIHs7Gw834uv0hhG+YhEI+Tk5PDDJ59mIDhM5YI5bF++BiQ8z0vsgu/7cV9rQULX2Y01yP+kThLOOTzPIxaLJfTOWjzfx1iLfB95+oQ+JSOd3NIiAAJZWVnU19ffkLaO9nbORy5R++wKjuz8PQAFBQXcN/M+eg72kJyczB1Tp3LkT0c4dLAHgGAwSPX91eTn53P06FH2de4jNS2VuXPncux4HwMDp5lUfht79+6luLiYiooKnHN0dnbS19eHdRbf8ymcOIGiKeWE+j7kzB/fJ2/sWEIfnObih3+NB1dcXKyhoSGNjIxoePiyTvafkuf5CofDkqTXd7yuzLH5Wvbmj3V75RcT1M6aNUuSFBoc1Eg0IkmKRKOaPWe20tPTdeDAAV0rz619XrcUjZUknejv10fDf9OePXtUUVGhCxcuJHDhcFiLFi8WoMqlC/XNLWt175I6zVxer7o1T+vBZxpVPG2yap5ZHY+laNw4hQYHJUlPNTUp1QV07vx5SdKO7TuUWVig1Yd3q6rpYQEKpqUIUFVVlWKxmHp7e3XX9Ol6ZNkySdLOXbv0ZFOTJGnlqlUqKSlRe0e7JGlp/VKFQiFJUktLixYtWqwTJ05oZGRENbU1qqqu1qWPLmloaEiT7pquJdtelA0kJTbt3oeX6uub16tgUrnu/0F8AQFjIC83l1de+gkvt/yGaQ99m0ULF1M3r5amdetYsmMLYyaWceXiFYyN0zp65p1ztLW18YeuLo4fP86mTRvJz8ujsrISz/OYP38+36irI5gSJBQKMWH8BNLT0+nu7qampoaionGUlZWx9913aNnVAsBb7R3Mq63lntkPcnjfIeTFCKakEo1GeH/P22QUlmIDyRglxe8A1rH6e6t47de7mffydvKnTWX3Y4/yyLLlfPed3xIsu4XocISPBy8h30/ksNFLaqzBOsuYtDR83yccDnPu3Dmcc2zauJHO997jaw88QPbNN7N//34aG58gFAphrcUYQzQapbi4hMysTKKRKLdNnIDvRThzop/sopL4PJERfN8nLa+ApNRMvKjwPQuAHTh1im2/+h31b7zNmOJyQv0D3LOygYfeaiOpaBxJLoX9zT+l5402jDX4VzNVUnISzjnS0tLirBgIuAA5uTm82NxMLBbjhfXreWnrNrZs3kxNbQ2h0CDOBcjMzML3fQYGTtPc3EzZrWX0ftBL7597mTJ5Cq+++jM6fvkLCkrHc2ftQpIyM8ibOImvfGs5BNNwzhJIHRNnYMaKRu6oWULr6hVUNKzmplvHE7k8RHrZZIIpjq7mZtrXbkikQV2l4OzZs7S2ttLV1QXA5XCYnbve5OTJk/T09DBjxgxWPv44JSWl/Gj9Czz37BqiUY/W1ha6u+OZylpLY2Mjx44dZ/6CBThrWfv8OrZu3UosEqHtqSf4cv0ySr90NxdDZzj4823cVFBINBzmL4cOxo/CnXPqdPvMagEqLP+CHn33sBr6B/X904Oa2dAgIF5IjPn3C91nYv+7MQzuRtj4TyApWYByPjde3+nYrxmPrYo7Oyv+SUDXVuJR3bV9a22i75xLBHS9z7W667HxyhsP3lgbb9fY4l9nZYi/b6xzeF6MlNR0Pr4yjDUO4SP9v14+/1r+DhnzL/FS2BMpAAAAAElFTkSuQmCCiVBORw0KGgoAAAANSUhEUgAAAEAAAAASCAYAAADrL9giAAABCGlDQ1BJQ0MgUHJvZmlsZQAAeJxjYGA8wQAELAYMDLl5JUVB7k4KEZFRCuwPGBiBEAwSk4sLGHADoKpv1yBqL+viUYcLcKakFicD6Q9ArFIEtBxopAiQLZIOYWuA2EkQtg2IXV5SUAJkB4DYRSFBzkB2CpCtkY7ETkJiJxcUgdT3ANk2uTmlyQh3M/Ck5oUGA2kOIJZhKGYIYnBncAL5H6IkfxEDg8VXBgbmCQixpJkMDNtbGRgkbiHEVBYwMPC3MDBsO48QQ4RJQWJRIliIBYiZ0tIYGD4tZ2DgjWRgEL7AwMAVDQsIHG5TALvNnSEfCNMZchhSgSKeDHkMyQx6QJYRgwGDIYMZAKbWPz9HbOBQAAAI10lEQVR4nN2Xa3BV1RXHf3ufc29ySbghAYpQEGqCFRgEy0SFYnkp7wrToqA8BVSgg4/BD2o7ICDTdoQZW5Sx+BjIQwojAiMv5S2tKLUqPhBBniHWAEmAAObee87598NJLkGgQ7/Zrpk9c87aa6+99n+vvfZ/G0A0EMO1iwxgDDaA4FI3P0ixhDFbxyHwAyRhAFlrkcIFXAsABursLRbwrCD4gQNgwritwG+gtsYYgiBEQxLBNTRfQtYSEIAVpsHijTEYYy79vwqs9bYN7Rv2Nfi56thrFYtBQKRxjIdfn88N3ToB4Epi5syZDBw4EN/3sY5F1GdDOIEUoucFPhHH5WR1NcOGDOHWUQPoM20UL/3qMc6cOoMxJp1JjuOkgQVwXAff90FgrcUYE/7XieOGaRnOp0v81NsZY3AcB8/zLumXRBAEF305DgQBvoSxBlu3Dosh8AOqyytIXqhN22vr1q36b2Tq1OnKap6jWXvf0NNbXlU8L0eAXNdVLBZTLBYTYW1RPCcuJ+IKkHVsWg8oI5ap3LxcRTMz0jpjjSLRiBplZSkajQpQNBpVNBqVteF4x3GUm5ur7Ozs9Lj6PmtNWhfJiF70ixOOxVwSA4DWrVsnz/OUSCSUSqUkSUEQyPM8+b6vVCqlRG1CkjThgQdEhqO5/1yuEb+fLmuMXBsRoGHDhunYsWP66OOPNHLUKO3YsUPHy8v1xd69emDSxHSg8Zy45s+fr4OHDurkqVPaf2C/5s57Vo0aNRKg15ctU9nx45o1d44GDR2iL/Z+ocLCQgGaPn269uzZo4qKCh09elSlpaVq3759GhhAt/xyoB4qfVFTly/W2MXzlX9bN93UvbsGTJkoa4zum/20mrVpfRGA9evXS5KSyaR8P9COd3eqouKkfN+X7/vyPE+S9PCUqTIZEf1u5zLd89yMEFljFImEAEyYMEGSlPK9K2ZO/wH9BWjbtm1pXc35c+nvlatWCdD7uz+QJJWXl6f7CgsLNW/evCv6Lf/mG+UXFAjQnVMn6cmdb6nzgD5q3q61CnreqrHPzdGUN4s1fMEcAXrs7ZVq2emnDQDYsF5BEEiS/r5rlwA9OOnhMMALYYDTpz8iIq6e2LJcT321QbZRhjBG1lq5bpjiY8aMCUELfJWUluqmDh00euxYVVVXKQgC/WXxyxowcKAkqbKqSv0HDBCg+0bfr5pzNZKkPn36aPOWzfJ9X5L01b59Kioq0uTJD9ZtkK83V72prl27avJDD+r06WpJ0iuvvqbMJrmauWurmrZrc0maW8fR9J1va/AfZgvQ5FXL9KMOIQAWIJlKYYyh7Jsyxo8eQ5tOXSgqLaJ4aTHZsSymPfYICxe9yKOrlhC75UbOV5whMxaDBsWqvkhZa0klU8x+5hn2ffklpcXF7P7HbowxNI43ZsiQoQRBQG2ill69evHsvHl069aNrKxsAPr164eX9LDW8vnnn9O9Rw/GjRtHPB4nEolQW3uBGU/M4JNPPuGVxS+zduNGJNGlY2c69e7NkX2HqDxSRtR1sMbiRDMIfJ89K9bSKDOcw9ooGBveAgB5eXlUnT5N3x49SbW4nonLS3l/yatMmfYbVq5eyYZNW3hoZTG5XTtxprIaG8vmSlIPRjKZxPO8umoPidoEAJFIlOzG2RhjiMVijBw1kmg0yvlz59i8eRMRN8Lhw4e5/fbbAdi9ezdVVVW4rkM8HicIAhK1Cc6erSESjZBKpqioOBECb6BJi1bUVJ3HWIuPMHW3g7GW785ewPfCRRO49XuPxRg2b9pKn593J9GyFeNeL+FErbht2iPcPGIEa1av4d7n5tGyRw9OVJ4mI55DqrySxLkLV72HjQlZRxAE+H6QtkvU1nJg/36MMVSeqqRjh45c37oN/frdydIlSykpKeGtt9YSjUaB8DozxuB5PocOHcJaS+N4Dn379iGVTBHPidO31y8IgoAz509zeM9ntGiXj4IAYw2OGyHiGBQENMsvwBi3bqOc9BVvLYY5s2dxIbcNk5dtpKbWIZIKqD5zjsIpUxnxwvM0vasnZ05Uk52bx/mvy3hjxiz8RPKSXYeQDnueR8r3CBoA4vk+nueRmRmluKiIZDJJQX4+77y9iWdmz2X79ncpKSlh0aJFRCIRgiC0D4LwiFlrWbduLceOHcN1XV5evJglS5ewddtWunbpirWWpUXFHPrgb2TGcym8dxxe0ifpJUkmkrTo0JmOQ0dTc7YmjCcgzXXcaGYGnYbeT+9Hn2L/hx/Q6meFXPiuGjdlME2bc8Pw4aSqzxJpHKO27Agrxj1OxcEjGGvQ9+hvRkYGruuSm9MEx9q0Ph6P47ou17VsyfHjx5k4cSILFy6kV6876NXrDgDKysqYNGkS5eXHycvLw3XddF1wXZfKykpGjhxJSUkJ+fn5jB83HoBUKsWCBQtYWlSMQax6cgYj/riI67oVUrl3D7G2N9CsUZwv16wgntMEgMaNsjA2EmZr7ymP6u4/PU/J/eP5eHUJo14qos2A4XxXfRIiPkr4RHMyCL49xl/HT+bbA/tDVuddZHH1DLD9jTfSv/9d1CYSrFi+nJqaEPGBgwZRkF/AwYNfs3FDWLTatm3L4MFD0qCsWbOaExUVGGMZOnQI7dq15bPP9rJ9+9b0EZJETk4Od989nIKCAs7WnGXTO+/w6ad70sdOgchq2oouI35Ns2Y/oaJ8Hx8vL6FJ8xbktb6e/e/tpPPgQRx8bxfnTldh2tx8qzre0ZPNr71AkEjiRrO458+v0HbgYM6e+hdOk1zMyaO8MWYc5Qf2YV0H1S3+mp4/5nLDhvT2cn1wVc/W2kso75X0jnXwg8t9p22B73uoo4jIsY4sKCOWrVFFy/XbqpQe3/WhWne6OX2fAldtxhi5rpvmBWnfjiPXddNMjTpGWG/ruq6MMZfZ19Pb789R3/+fbIzjyNa1tC5Nl62on89aI+s6oQFWNhIOyMiKa/ic+fpxl67XtPj/1WbCV6LBCgITvpeNcfDlpVPEOC7GD8Ln7/+Z/BtvuZsKG8gwgwAAAABJRU5ErkJggg=="

class NeroAIClient:
    def __init__(self, root):
        self.root    = root
        self.root.title("NeroAI — IBKR CopyTrade")
        self.root.geometry("860x700")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.ib        = IB()
        self.running   = False
        self.placed    = set()
        self._stop     = threading.Event()
        self._counts   = {"received": 0, "placed": 0, "failed": 0}
        self._mode     = tk.StringVar(value="new")   # "new" or "all"
        self._startup_orders_loaded = False
        self._build_ui()
        self._set_icon()

    def _set_icon(self):
        try:
            import tempfile
            ico_data = base64.b64decode(ICON_B64)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ico")
            tmp.write(ico_data)
            tmp.close()
            self.root.iconbitmap(tmp.name)
        except: pass

    def _build_ui(self):
        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=PANEL2)
        hdr.pack(fill="x")
        stripe = tk.Canvas(hdr, height=3, bg=BG, highlightthickness=0)
        stripe.pack(fill="x")
        for i in range(860):
            g = int(0xd4 + (0xc8 - 0xd4) * i / 860)
            b = int(0xaa + (0xff - 0xaa) * i / 860)
            stripe.create_line(i, 0, i, 3, fill=f"#00{g:02x}{b:02x}")
        inner = tk.Frame(hdr, bg=PANEL2, padx=20, pady=12)
        inner.pack(fill="x")
        img_data = base64.b64decode(LOGO_B64)
        pil_img  = Image.open(io.BytesIO(img_data))
        self._logo_img = ImageTk.PhotoImage(pil_img)
        tk.Label(inner, image=self._logo_img, bg=PANEL2, bd=0).pack(side="left")
        tk.Label(inner, text="  CopyTrade Engine",
                 font=("Segoe UI", 9), fg=SUB, bg=PANEL2).pack(side="left")
        self._time_lbl = tk.Label(inner, text="", font=("Courier New", 9), fg=SUB, bg=PANEL2)
        self._time_lbl.pack(side="right")
        self._tick_clock()
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # ── status ────────────────────────────────────────────────────────────
        sbar = tk.Frame(self.root, bg=BG, padx=24, pady=10)
        sbar.pack(fill="x")
        self._dot = tk.Label(sbar, text="●", font=("Segoe UI", 14), fg=RED, bg=BG)
        self._dot.pack(side="left")
        self._status_lbl = tk.Label(sbar, text="  Disconnected",
                                     font=("Segoe UI", 10, "bold"), fg=RED, bg=BG)
        self._status_lbl.pack(side="left")
        self._bal_lbl = tk.Label(sbar, text="Net Liquidation:  —",
                                  font=("Segoe UI", 10), fg=SUB, bg=BG)
        self._bal_lbl.pack(side="right")

        # ── connection panel ──────────────────────────────────────────────────
        cp = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        cp.pack(fill="x", padx=24, pady=(4, 10))
        ci = tk.Frame(cp, bg=PANEL, padx=20, pady=14)
        ci.pack(fill="x")
        tk.Label(ci, text="TWS CONNECTION", font=("Segoe UI", 7, "bold"),
                 fg=TEAL, bg=PANEL).grid(row=0, column=0, columnspan=7, sticky="w", pady=(0,8))
        self._fields = {}
        for col, (lbl, val, w) in enumerate([("Host","127.0.0.1",16),("Port","7496",8),("Client ID","20",8)]):
            tk.Label(ci, text=lbl, font=("Segoe UI", 8), fg=SUB, bg=PANEL).grid(row=1, column=col*2, sticky="w", padx=(0,4))
            e = tk.Entry(ci, font=("Segoe UI", 10), bg="#0a1220", fg=TEXT,
                         insertbackground=TEAL, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=TEAL, width=w)
            e.insert(0, val)
            e.grid(row=2, column=col*2, padx=(0,20), ipady=6)
            self._fields[lbl] = e
        self._btn = tk.Button(ci, text="▶   START", font=("Segoe UI", 10, "bold"),
                               bg=TEAL, fg="#0a1220", relief="flat",
                               activebackground="#00e8c0", activeforeground="#0a1220",
                               cursor="hand2", padx=24, pady=7, command=self._toggle)
        self._btn.grid(row=2, column=6)

        # ── trade mode toggle ─────────────────────────────────────────────────
        mode_frame = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        mode_frame.pack(fill="x", padx=24, pady=(0, 10))
        mf_inner = tk.Frame(mode_frame, bg=PANEL, padx=20, pady=12)
        mf_inner.pack(fill="x")
        tk.Label(mf_inner, text="COPY MODE", font=("Segoe UI", 7, "bold"),
                 fg=TEAL, bg=PANEL).pack(side="left", padx=(0, 20))

        for value, label in [("new", "New Trades Only"), ("all", "Existing + New Trades")]:
            rb = tk.Radiobutton(
                mf_inner, text=label, variable=self._mode, value=value,
                font=("Segoe UI", 9), fg=TEXT, bg=PANEL,
                selectcolor=DIM2, activebackground=PANEL, activeforeground=TEAL,
                indicatoron=0, relief="flat", cursor="hand2",
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=TEAL, padx=14, pady=6,
                command=self._on_mode_change
            )
            rb.pack(side="left", padx=(0, 8))

        self._mode_lbl = tk.Label(mf_inner, text="",
                                   font=("Segoe UI", 8), fg=SUB, bg=PANEL)
        self._mode_lbl.pack(side="left", padx=(10, 0))
        self._on_mode_change()

        # ── stat cards ────────────────────────────────────────────────────────
        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=24, pady=(0, 10))
        self._stat_labels = {}
        for i, (title, key, color) in enumerate([
                ("ORDERS RECEIVED","received",CYAN),
                ("ORDERS PLACED","placed",TEAL),
                ("FAILED","failed",RED)]):
            f = tk.Frame(cards, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            f.pack(side="left", fill="x", expand=True, padx=(0 if i==0 else 10, 0))
            tk.Label(f, text=title, font=("Segoe UI", 7, "bold"), fg=SUB, bg=PANEL).pack(pady=(10,0))
            v = tk.Label(f, text="0", font=("Courier New", 22, "bold"), fg=color, bg=PANEL)
            v.pack(pady=(2,10))
            self._stat_labels[key] = v

        # ── log ───────────────────────────────────────────────────────────────
        lf = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        lf.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        lf_hdr = tk.Frame(lf, bg=BORDER, padx=16, pady=6)
        lf_hdr.pack(fill="x")
        tk.Label(lf_hdr, text="LIVE ORDER FEED",
                 font=("Segoe UI", 8, "bold"), fg=TEAL, bg=BORDER).pack(side="left")
        clr = tk.Label(lf_hdr, text="clear", font=("Segoe UI", 8), fg=SUB, bg=BORDER, cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda e: self._clear_log())

        self.log = scrolledtext.ScrolledText(
            lf, font=("Consolas", 9), bg="#080e1a", fg=TEXT,
            insertbackground=TEAL, relief="flat", bd=0,
            state="disabled", wrap="none", padx=14, pady=10)
        self.log.pack(fill="both", expand=True)

        # log tags
        self.log.tag_config("ok",     foreground=GREEN)
        self.log.tag_config("err",    foreground=RED)
        self.log.tag_config("info",   foreground=CYAN)
        self.log.tag_config("warn",   foreground=YELLOW)
        self.log.tag_config("dim",    foreground=SUB)
        self.log.tag_config("buy",    foreground="#00ff99")
        self.log.tag_config("sell",   foreground="#ff4060")
        self.log.tag_config("symbol", foreground=WHITE)
        self.log.tag_config("price",  foreground=CYAN)

        self._log_info("NeroAI CopyTrade Engine ready. Configure connection and press START.")

    # ── mode ──────────────────────────────────────────────────────────────────
    def _on_mode_change(self):
        if self._mode.get() == "new":
            self._mode_lbl.config(text="Only orders placed after START will be mirrored")
        else:
            self._mode_lbl.config(text="All current open orders + new orders will be mirrored")

    # ── clock ─────────────────────────────────────────────────────────────────
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

    def _log_info(self, msg):
        self._log_raw([(msg, "info")])

    def _log_err(self, msg):
        self._log_raw([(msg, "err")])

    def _log_warn(self, msg):
        self._log_raw([(msg, "warn")])

    def _log_order(self, o):
        action = o["action"]
        tag = "buy" if action == "BUY" else "sell"
        self._log_raw([
            (f"{action:<4s}  ", tag),
            (f"{o['symbol']:<6s}", "symbol"),
            (f"  qty={o['quantity']}  {o['orderType']} @ ", "dim"),
            (f"{o['price']}", "price"),
        ])

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    # ── status ────────────────────────────────────────────────────────────────
    def _set_status(self, connected):
        c = GREEN if connected else RED
        t = "  Connected  —  Mirroring active" if connected else "  Disconnected"
        self._dot.config(fg=c)
        self._status_lbl.config(text=t, fg=c)

    def _inc(self, key):
        self._counts[key] += 1
        self._stat_labels[key].config(text=str(self._counts[key]))

    # ── start/stop ────────────────────────────────────────────────────────────
    def _toggle(self):
        if not self.running: self._start()
        else: self._stop_engine()

    def _start(self):
        host = self._fields["Host"].get().strip()
        port = int(self._fields["Port"].get().strip())
        cid  = int(self._fields["Client ID"].get().strip())
        self._btn.config(text="■   STOP", bg=RED, activebackground="#cc2244", fg=WHITE)
        self._log_info(f"Connecting to TWS  {host}:{port}  clientId={cid} …")
        threading.Thread(target=self._run, args=(host, port, cid), daemon=True).start()

    def _stop_engine(self):
        self._stop.set()
        self.running = False
        self._startup_orders_loaded = False
        self._btn.config(text="▶   START", bg=TEAL, activebackground="#00e8c0", fg="#0a1220")
        self.root.after(0, lambda: self._set_status(False))
        self._log_warn("Engine stopped.")
        try: self.ib.disconnect()
        except: pass

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
            self._fetch_balance()
        except Exception as e:
            self.root.after(0, lambda: self._log_err(f"Connection failed: {e}"))
            self.root.after(0, lambda: self._btn.config(text="▶   START", bg=TEAL, fg="#0a1220"))
            return

        # If mode=new, mark all existing orders as already seen (don't place them)
        if self._mode.get() == "new":
            try:
                existing = requests.get(VPS_URL, timeout=4).json()
                for o in existing:
                    key = o.get("id", f"{o['symbol']}-{o['action']}-{o['quantity']}-{o['price']}")
                    self.placed.add(key)
                self._log_info(f"Mode: New Trades Only — skipped {len(existing)} existing orders")
            except: pass

        while not self._stop.is_set():
            try:
                orders = requests.get(VPS_URL, timeout=4).json()
                for o in orders:
                    self._maybe_place(o)
            except Exception as e:
                self.root.after(0, lambda e=e: self._log_err(f"VPS poll error: {e}"))
            time.sleep(2)

    def _fetch_balance(self):
        try:
            for v in self.ib.accountValues():
                if v.tag == "NetLiquidation" and v.currency == "USD":
                    bal = f"${float(v.value):,.2f}"
                    self.root.after(0, lambda b=bal: self._bal_lbl.config(
                        text=f"Net Liquidation:  {b}", fg=TEXT))
                    return
        except: pass

    def _maybe_place(self, o):
        key = o.get("id", f"{o['symbol']}-{o['action']}-{o['quantity']}-{o['price']}")
        if key in self.placed: return
        self.placed.add(key)
        self.root.after(0, lambda: self._inc("received"))
        try:
            contract = Stock(o["symbol"], o["exchange"], o["currency"])
            order = MarketOrder(o["action"], o["quantity"]) if o["orderType"] == "MKT" \
                    else LimitOrder(o["action"], o["quantity"], o["price"])
            self.ib.placeOrder(contract, order)
            self.root.after(0, lambda: self._inc("placed"))
            self.root.after(0, lambda oo=o: self._log_order(oo))
        except Exception as e:
            self.root.after(0, lambda: self._inc("failed"))
            self.root.after(0, lambda e=e: self._log_err(f"Order error: {e}"))

if __name__ == "__main__":
    root = tk.Tk()
    NeroAIClient(root)
    root.mainloop()