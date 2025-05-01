
import tkinter as tk
from tkinter import ttk, font
import numpy as np
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import traceback
import time
import matplotlib
matplotlib.use('TkAgg')  # Ensure Tk backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ================================
# Summer‑Coolness Color Palette
# ================================
COLORS = {
    "bg_dark": "#4682B4",   # Steel Blue (darkest swatch)
    "bg_medium": "#B0E0E6", # Powder Blue (middle‑light swatch)
    "bg_light": "#E0FFFF",  # Light Cyan  (lightest swatch)
    "text": "#333333",       # Standard dark text
    "accent": "#87CEFA",     # Light Sky Blue (accent / highlights)
    "positive": "#27AE60",  # Green (unchanged)
    "negative": "#E74C3C",  # Red   (unchanged)
    "neutral": "#F39C12",   # Orange (unchanged)
    "header": "#4682B4",    # Same as bg_dark for titles
    "border": "#BDC3C7",   # Light gray for subtle borders
}

# -------------------------------------------------
# Simulated stock universe & data‑generation helpers
# -------------------------------------------------
STOCK_DATA_CACHE: dict[str, pd.DataFrame] = {}
STOCKS = [
    ("Apple Inc.", "AAPL"),
    ("Microsoft Corporation", "MSFT"),
    ("Alphabet Inc.", "GOOGL"),
    ("Amazon.com Inc.", "AMZN"),
    ("Meta Platforms Inc.", "META"),
    ("Tesla Inc.", "TSLA"),
    ("NVIDIA Corporation", "NVDA"),
    ("JPMorgan Chase & Co.", "JPM"),
    ("Bank of America Corp.", "BAC"),
    ("Visa Inc.", "V"),
]
DEFAULT_STOCK = "AAPL"

def generate_stock_data(ticker: str, days: int = 180) -> pd.DataFrame:
    """Return *simulated* OHLCV dataframe for a given ticker."""
    try:
        if ticker in STOCK_DATA_CACHE:
            return STOCK_DATA_CACHE[ticker]

        np.random.seed(abs(hash(ticker)) % 10_000)
        end_date = datetime.now()
        idx = pd.date_range(end=end_date, periods=days, freq="D")

        start_price = np.random.randint(50, 500)
        pct_change = np.random.normal(loc=0, scale=0.015, size=len(idx))
        trend = (abs(hash(ticker)) % 7 - 3) / 100  # deterministic slight trend
        pct_change += trend
        prices = start_price * (1 + pct_change).cumprod()

        df = pd.DataFrame(index=idx)
        df["Date"] = idx
        df["Close"] = prices
        df["Open"] = prices * (1 + np.random.uniform(-0.01, 0.01, len(prices)))
        daily_vol = prices * np.random.uniform(0.005, 0.02, len(prices))
        df["High"] = np.maximum(df["Open"], df["Close"]) + daily_vol
        df["Low"] = np.minimum(df["Open"], df["Close"]) - daily_vol
        df["Volume"] = np.random.randint(500, 9000, len(prices))

        STOCK_DATA_CACHE[ticker] = df
        return df
    except Exception as e:
        print("Data generation error:", e)
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

# -----------------------
# Technical‑indicator math
# -----------------------

def calculate_sma(data: pd.DataFrame, period: int = 20):
    return data["Close"].rolling(window=period).mean()

def calculate_ema(data: pd.DataFrame, period: int = 20):
    return data["Close"].ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.DataFrame, period: int = 14):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ------------------------
# Custom tick‑box widget
# ------------------------
class CheckmarkButton(ttk.Frame):
    def __init__(self, master, text: str, variable: tk.BooleanVar, command=None):
        super().__init__(master)
        self.variable = variable
        self.command = command

        box = tk.Label(self, text=" ", width=2, relief="solid", bg="white")
        box.pack(side=tk.LEFT, padx=(0, 5))
        label = ttk.Label(self, text=text)
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for widget in (box, label, self):
            widget.bind("<Button-1>", self._toggle)
        self._update()
        self.variable.trace_add("write", self._update)

    def _toggle(self, _=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _update(self, *_):
        mark = "√" if self.variable.get() else " "
        bg   = "#DFF0D8" if self.variable.get() else "white"
        border = 2 if self.variable.get() else 1
        self.winfo_children()[0].configure(text=mark, bg=bg, borderwidth=border)

# -------------------
# Main application UI
# -------------------
class FinancialAnalyticsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.configure(bg=COLORS["bg_dark"])
        self.current_stock = None
        self.stock_data: pd.DataFrame | None = None
        self.loading = False
        self._init_fonts()
        self._init_styles()
        self._build_ui()
        self._preload_default()

    # Font + style helpers
    def _init_fonts(self):
        self.title_font   = font.Font(family="Arial", size=14, weight="bold")
        self.header_font  = font.Font(family="Arial", size=12, weight="bold")
        default_font = font.nametofont("TkDefaultFont"); default_font.configure(size=10, family="Arial")

    def _init_styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TFrame", background=COLORS["bg_medium"])
        s.configure("Card.TFrame", background=COLORS["bg_medium"], relief="raised")
        s.configure("Header.TLabel", background=COLORS["bg_medium"], foreground=COLORS["header"], font=self.header_font)
        s.configure("Title.TLabel", background=COLORS["bg_medium"], foreground=COLORS["header"], font=self.title_font)
        s.configure("Nav.TButton", background=COLORS["bg_light"], foreground=COLORS["text"])
        s.map("Nav.TButton", background=[("active", COLORS["accent"])])
        s.configure("Active.Nav.TButton", background=COLORS["accent"], foreground=COLORS["text"])
        s.configure("StockInfo.TFrame", background="#2C3E50")
        s.configure("StockInfo.TLabel", background="#2C3E50", foreground="white")

    # ------------ UI construction ------------
    def _build_ui(self):
        main = ttk.Frame(self.root); main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        title = ttk.Frame(main); title.pack(fill=tk.X)
        ttk.Label(title, text="Financial Data Analytics", style="Title.TLabel").pack(side=tk.LEFT)

        content = ttk.Frame(main); content.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(content, width=300); left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10)); left.pack_propagate(False)
        self._build_stock_card(left)
        self._build_indicator_card(left)
        self._build_nav_card(left)

        self.right = ttk.Frame(content); self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.frames = {k: ttk.Frame(self.right) for k in ("overview","historical","recommendation")}
        self._build_overview(self.frames["overview"])
        self._build_historical(self.frames["historical"])
        self._build_recommendation(self.frames["recommendation"])
        self._show_section("overview")

    # ----- left column -----
    def _build_stock_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(card, text="Stock Selection", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=15, pady=10)
        ttk.Label(inner, text="Select Stock:").pack(anchor=tk.W)
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(inner, textvariable=self.stock_var, state="readonly", width=30)
        self.stock_combo["values"] = [f"{n} | {t}" for n,t in STOCKS]
        self.stock_combo.pack(fill=tk.X, pady=3)
        self.stock_combo.bind("<<ComboboxSelected>>", self.on_stock_selected)
        # Loading hint
        self.loading_frame = ttk.Frame(inner); ttk.Label(self.loading_frame, text="Loading data...").pack(anchor=tk.W)

    def _build_indicator_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(card, text="Technical Indicators", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=15, pady=5)
        self.indicators = {k: {"var": tk.BooleanVar(value=False), "name": n} for k,n in [
            ("sma","Simple Moving Average (SMA)"),("ema","Exponential Moving Average (EMA)"),
            ("boll","Bollinger Bands"),("rsi","Relative Strength Index (RSI)"),
        ]}
        for key,d in self.indicators.items():
            CheckmarkButton(inner, d["name"], d["var"], command=self.update_price_chart).pack(fill=tk.X, anchor=tk.W, pady=2)

    def _build_nav_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(card, text="Navigation", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=15, pady=5)
        self.nav_btns = {}
        for key,text in [("overview","Overview"),("historical","Historical Data"),("recommendation","Investment Recommendation")]:
            b = ttk.Button(inner, text=text, style="Nav.TButton", command=lambda k=key:self._show_section(k))
            b.pack(fill=tk.X, pady=2); self.nav_btns[key]=b

    # ----- right column frames -----
    def _build_overview(self, parent):
        self._stock_info_card(parent)
        self._price_chart_card(parent)

    def _build_historical(self, parent):
        self._candlestick_card(parent)
        self._hist_table_card(parent)

    def _build_recommendation(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(card, text="Investment Recommendation", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.rec_text = tk.Text(inner, wrap=tk.WORD, bg=COLORS["bg_medium"], fg=COLORS["text"], bd=0)
        self.rec_text.insert("1.0","Select a stock to view investment recommendations.")
        self.rec_text.configure(state=tk.DISABLED)
        self.rec_text.pack(fill=tk.BOTH, expand=True)

    # --- cards helpers ---
    def _stock_info_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(card, text="Stock Information", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card, style="StockInfo.TFrame"); inner.pack(fill=tk.X, padx=15, pady=10)
        self.info_lbls = {}
        self.info_lbls["company"] = ttk.Label(inner, text="Company (TICKER)", style="StockInfo.TLabel", font=("Arial",16,"bold")); self.info_lbls["company"].pack(anchor=tk.W)
        price_frame = ttk.Frame(inner, style="StockInfo.TFrame"); price_frame.pack(anchor=tk.W)
        self.info_lbls["price"] = ttk.Label(price_frame, text="$0.00", style="StockInfo.TLabel", font=("Arial",20,"bold")); self.info_lbls["price"].pack(side=tk.LEFT)
        self.info_lbls["change"] = ttk.Label(price_frame, text="+0.00 (0.00%)", style="StockInfo.TLabel", font=("Arial",14)); self.info_lbls["change"].pack(side=tk.LEFT, padx=10)
        # extra stats
        stats = ttk.Frame(inner, style="StockInfo.TFrame"); stats.pack(anchor=tk.W, pady=5)
        for key, lbl in [("open","Open"),("dayhigh","Day High"),("daylow","Day Low"),("volume","Volume")]:
            f = ttk.Frame(stats, style="StockInfo.TFrame"); f.pack(side=tk.LEFT, padx=8)
            ttk.Label(f, text=f"{lbl}:", style="StockInfo.TLabel", font=("Arial",10,"bold")).pack(anchor=tk.W)
            self.info_lbls[key] = ttk.Label(f, text="--", style="StockInfo.TLabel"); self.info_lbls[key].pack(anchor=tk.W)

    def _price_chart_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(card, text="Price Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.fig, self.ax = plt.subplots(figsize=(6,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=inner); self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax.text(0.5,0.5,"Select a stock", ha="center", va="center", transform=self.ax.transAxes)
        self.ax.set_xticks([]); self.ax.set_yticks([])

    def _candlestick_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(card, text="Candlestick Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=15, pady=10)
        self.hist_fig, self.hist_ax = plt.subplots(figsize=(6,3), dpi=100)
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=inner); self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.hist_ax.text(0.5,0.5,"Select a stock", ha="center", va="center", transform=self.hist_ax.transAxes)
        self.hist_ax.set_xticks([]); self.hist_ax.set_yticks([])

    def _hist_table_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(card, text="Historical Data", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10,5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        cols = ("Date","Open","High","Low","Close","Volume")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings", height=12)
        for c in cols: self.tree.heading(c,text=c); self.tree.column(c,width=100,anchor=tk.CENTER)
        sb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview); self.tree.configure(yscroll=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); sb.pack(side=tk.RIGHT, fill=tk.Y)

    # ------------------------- event handlers -------------------------
    def on_stock_selected(self, _):
        if self.loading: return
        selection = self.stock_combo.get()
        if not selection: return
        company,ticker = selection.split(" | ")
        self._show_loading()
        threading.Thread(target=self._load_data, args=(company,ticker), daemon=True).start()

    def _load_data(self, company, ticker):
        time.sleep(0.05)
        self.stock_data = generate_stock_data(ticker)
        self.current_stock = ticker
        self.root.after(0, lambda: self._update_all(company,ticker))

    def _update_all(self, company, ticker):
        self._update_info(company,ticker)
        if self.section=="overview":
            self.update_price_chart()
        elif self.section=="historical":
            self._update_historical()
        elif self.section=="recommendation":
            self._update_recommendation()
        self._hide_loading()

    # Loading helpers
    def _show_loading(self):
        self.loading=True; self.loading_frame.pack(fill=tk.X, pady=4); self.root.update_idletasks()
    def _hide_loading(self):
        self.loading=False; self.loading_frame.pack_forget(); self.root.update_idletasks()

    # Switch nav section
    def _show_section(self, key):
        self.section = key
        for k,b in self.nav_btns.items():
            b.configure(style="Active.Nav.TButton" if k==key else "Nav.TButton")
        for f in self.frames.values(): f.pack_forget()
        self.frames[key].pack(fill=tk.BOTH, expand=True)
        # refresh existing view
        if self.current_stock:
            if key=="overview": self.update_price_chart()
            elif key=="historical": self._update_historical()
            elif key=="recommendation": self._update_recommendation()

    # Info panel update
    def _update_info(self, company,ticker):
        if self.stock_data is None or self.stock_data.empty: return
        latest = self.stock_data.iloc[-1]; prev = self.stock_data.iloc[-2]
        change = latest.Close-prev.Close; pct=change/prev.Close*100
        self.info_lbls["company"].configure(text=f"{company} ({ticker})")
        self.info_lbls["price"].configure(text=f"${latest.Close:,.2f}")
        fg="green" if change>=0 else "red"
        self.info_lbls["change"].configure(text=f"{change:+.2f} ({pct:+.2f}%)", foreground=fg)
        self.info_lbls["open"].configure(text=f"${latest.Open:,.2f}")
        self.info_lbls["dayhigh"].configure(text=f"${latest.High:,.2f}")
        self.info_lbls["daylow"].configure(text=f"${latest.Low:,.2f}")
        self.info_lbls["volume"].configure(text=f"{int(latest.Volume):,}")

    # -------- charts & tables --------
    def update_price_chart(self):
        if self.stock_data is None: return
        self.ax.clear()
        subset = self.stock_data.iloc[-90:]
        self.ax.plot(subset.index, subset.Close, color=COLORS["accent"], linewidth=2, label="Price")
        # indicators
        if self.indicators["sma"]["var"].get():
            self.ax.plot(subset.index, calculate_sma(subset), linestyle="--", color="green", label="SMA(20)")
        if self.indicators["ema"]["var"].get():
            self.ax.plot(subset.index, calculate_ema(subset), linestyle="--", color="red", label="EMA(20)")
        if any(v["var"].get() for v in self.indicators.values()):
            self.ax.legend(loc="upper left")
        self.ax.set_title(f"{self.current_stock} - Price Chart", color=COLORS["header"])
        self.ax.set_xlabel("Date"); self.ax.set_ylabel("Price ($)")
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        self.fig.tight_layout(); self.canvas.draw()

    def _update_historical(self):
        self._update_candles(); self._update_table()

    def _update_candles(self):
        self.hist_ax.clear()
        sub = self.stock_data.iloc[-30:]
        for idx,row in sub.iterrows():
            color = COLORS["positive"] if row.Close>=row.Open else COLORS["negative"]
            self.hist_ax.plot([idx,idx],[row.Low,row.High], color=color, linewidth=1)
            self.hist_ax.bar(idx, row.Close-row.Open, bottom=row.Open, color=color, width=0.8, alpha=0.6)
        self.hist_ax.set_title(f"{self.current_stock} - Candlestick", color=COLORS["header"])
        self.hist_ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d")); self.hist_ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        self.hist_fig.tight_layout(); self.hist_canvas.draw()

    def _update_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for _,row in self.stock_data.iloc[::-1].head(100).iterrows():
            self.tree.insert("", tk.END, values=(row.name.strftime("%Y-%m-%d"), f"${row.Open:.2f}", f"${row.High:.2f}", f"${row.Low:.2f}", f"${row.Close:.2f}", f"{int(row.Volume):,}"))

    def _update_recommendation(self):
        if self.stock_data is None: return
        current = self.stock_data.Close.iloc[-1]; rsi = calculate_rsi(self.stock_data).iloc[-1]
        sma20 = calculate_sma(self.stock_data,20).iloc[-1]
        rec = "BUY" if current>sma20 and rsi<70 else "SELL" if current<sma20 and rsi>30 else "HOLD"
        self.rec_text.configure(state=tk.NORMAL); self.rec_text.delete("1.0", tk.END)
        self.rec_text.insert(tk.END, f"Recommendation: {rec}\nCurrent Price: ${current:.2f}\nRSI(14): {rsi:.1f}\n20‑day SMA: ${sma20:.2f}\n")
        self.rec_text.configure(state=tk.DISABLED)

    # ---------- preload default ----------
    def _preload_default(self):
        def task():
            generate_stock_data(DEFAULT_STOCK); self.root.after(300, lambda:self.stock_combo.current([t for n,t in STOCKS].index(DEFAULT_STOCK)) or self.on_stock_selected(None))
        threading.Thread(target=task, daemon=True).start()

# ------------------------- main -------------------------
if __name__ == "__main__":
    root = tk.Tk(); root.title("Financial Data Analytics Software")
    try:
        FinancialAnalyticsApp(root); root.mainloop()
    except Exception as e:
        traceback.print_exc(); tk.messagebox.showerror("Error", str(e))

