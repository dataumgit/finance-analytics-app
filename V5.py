import tkinter as tk
from tkinter import ttk, font, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import threading, time, traceback

# ---------- 主题配色 ----------
COLORS = {
    "bg_dark": "#2C3E50",
    "bg_medium": "#FFFFFF",
    "bg_light": "#F4F6F9",
    "text": "#333333",
    "accent": "#3498DB",
    "positive": "#27AE60",
    "negative": "#E74C3C",
    "neutral":  "#F39C12",
    "header":  "#2C3E50",
    "border":  "#BDC3C7",
}

# ---------- 演示股票池 ----------
STOCKS = [
    ("Apple Inc.",             "AAPL"),
    ("Microsoft Corporation",  "MSFT"),
    ("Alphabet Inc.",          "GOOGL"),
    ("Amazon.com Inc.",        "AMZN"),
    ("Meta Platforms Inc.",    "META"),
    ("Tesla Inc.",             "TSLA"),
    ("NVIDIA Corporation",     "NVDA"),
    ("JPMorgan Chase & Co.",   "JPM"),
    ("Bank of America Corp.",  "BAC"),
    ("Visa Inc.",              "V"),
]
DEFAULT_STOCK = "AAPL"
_CACHE = {}  # 简单内存缓存


# ---------- 数据生成 ----------
def generate_stock_data(ticker: str, days: int = 180) -> pd.DataFrame:
    if ticker in _CACHE:
        return _CACHE[ticker]

    rng = np.random.default_rng(abs(hash(ticker)) % 2**32)
    idx = pd.date_range(end=datetime.now(), periods=days, freq="D")
    start_price = rng.uniform(50, 300)
    pct = rng.normal(0, 0.015, len(idx)) + (hash(ticker) % 7 - 3) / 100
    price = start_price * (1 + pct).cumprod()

    df = pd.DataFrame(index=idx)
    df["Close"] = price
    df["Open"] = price * rng.uniform(0.99, 1.01, len(price))
    vol = price * rng.uniform(0.005, 0.02, len(price))
    df["High"] = np.maximum(df["Open"], df["Close"]) + vol
    df["Low"]  = np.minimum(df["Open"], df["Close"]) - vol
    df["Volume"] = rng.integers(800, 9000, len(price))
    _CACHE[ticker] = df
    return df


# ---------- 技术指标 ----------
def sma(s: pd.Series, n=20): return s.rolling(n).mean()
def ema(s: pd.Series, n=20): return s.ewm(span=n, adjust=False).mean()
def rsi(s: pd.Series, n=14):
    d = s.diff(); gain = d.clip(lower=0); loss = -d.clip(upper=0)
    rs = gain.rolling(n).mean() / loss.rolling(n).mean()
    return 100 - 100/(1+rs)


# ---------- 自定义复选按钮 ----------
class Checkmark(ttk.Frame):
    def __init__(self, master, text, var: tk.BooleanVar, cmd):
        super().__init__(master)
        box = tk.Label(self, width=2, relief="solid", bg="white")
        box.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(self, text=text).pack(side=tk.LEFT, fill=tk.X, expand=True)
        for w in (box, self): w.bind("<Button-1>", lambda *_: self.toggle(cmd))
        self.var = var
        self.box = box
        self.var.trace_add("write", self.refresh); self.refresh()

    def toggle(self, cmd):
        self.var.set(not self.var.get()); cmd()
    def refresh(self, *_):
        if self.var.get(): self.box.configure(text="√", bg="#DFF0D8", bd=2)
        else:               self.box.configure(text=" ", bg="white",  bd=1)


# ---------- 主应用 ----------
class FinancialAnalyticsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.current_stock = ""
        self.stock_data: pd.DataFrame | None = None
        self.loading = False
        self.current_view = "overview"

        self._init_fonts()
        self._init_styles()
        self._build_ui()
        self._preload_default()

    # ========== 界面基础 ==========
    def _init_fonts(self):
        font.nametofont("TkDefaultFont").configure(size=10, family="Arial")
        self.f_header = font.Font(family="Arial", size=12, weight="bold")
        self.f_title  = font.Font(family="Arial", size=14, weight="bold")

    def _init_styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TFrame", background=COLORS["bg_medium"])
        s.configure("Card.TFrame", background=COLORS["bg_medium"], relief="ridge")
        s.configure("Header.TLabel", background=COLORS["bg_medium"],
                    foreground=COLORS["header"], font=self.f_header)
        s.configure("Title.TLabel", background=COLORS["bg_medium"],
                    foreground=COLORS["header"], font=self.f_title)
        s.configure("Nav.TButton", background=COLORS["bg_light"])
        s.configure("Active.Nav.TButton", background=COLORS["accent"], foreground="white")

        s.configure("StockInfo.TFrame", background="#2C3E50")
        s.configure("StockInfo.TLabel", background="#2C3E50", foreground="white")

    # ========== 构建 UI ==========
    def _build_ui(self):
        main = ttk.Frame(self.root); main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Label(main, text="Financial Data Analytics", style="Title.TLabel")\
            .pack(anchor=tk.W, pady=(0,5))

        body = ttk.Frame(main); body.pack(fill=tk.BOTH, expand=True)

        # 左侧面板
        left = ttk.Frame(body, width=260); left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8))
        left.pack_propagate(False)
        self._card_stock_select(left)
        self._card_indicators(left)
        self._card_nav(left)

        # 右侧多视图
        self.right = ttk.Frame(body); self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.frames = {k: ttk.Frame(self.right) for k in ("overview","historical","recommendation")}
        self._card_stock_info(self.frames["overview"])
        self._card_price_chart(self.frames["overview"])
        self._card_candles(self.frames["historical"])
        self._card_hist_table(self.frames["historical"])
        self._card_recom(self.frames["recommendation"])
        self._show_view("overview")

    # ----- 卡片组件 -----
    def _card_stock_select(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5)
        ttk.Label(card, text="Stock Selection", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=12, pady=6)

        ttk.Label(inner, text="Select Stock:").pack(anchor=tk.W)
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(inner, textvariable=self.stock_var, state="readonly",
                                        values=[f"{n} | {t}" for n,t in STOCKS])
        self.stock_combo.pack(fill=tk.X, pady=2)
        self.stock_combo.bind("<<ComboboxSelected>>", self.on_stock_selected)

        self.loading_lbl = ttk.Label(inner, text="Loading...", foreground=COLORS["accent"])
        self.loading_lbl.pack(anchor=tk.W, pady=2); self.loading_lbl.pack_forget()

    def _card_indicators(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5)
        ttk.Label(card, text="Technical Indicators", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=12, pady=6)

        self.ind_vars = {
            "sma": tk.BooleanVar(value=True),
            "ema": tk.BooleanVar(value=False),
            "boll": tk.BooleanVar(value=False),
            "rsi": tk.BooleanVar(value=False),
        }
        names = {"sma":"Simple Moving Average","ema":"Exponential Moving Average",
                 "boll":"Bollinger Bands","rsi":"RSI"}
        for k in self.ind_vars:
            Checkmark(inner, names[k], self.ind_vars[k], self.update_price_chart)\
                .pack(fill=tk.X, anchor=tk.W, pady=2)

    def _card_nav(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5)
        ttk.Label(card, text="Navigation", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=12, pady=6)
        self.nav_buttons = {}
        for key, txt in [("overview","Overview"),("historical","Historical Data"),
                         ("recommendation","Recommendation")]:
            b = ttk.Button(inner, text=txt, style="Nav.TButton",
                           command=lambda k=key:self._show_view(k))
            b.pack(fill=tk.X, pady=2); self.nav_buttons[key]=b

    def _card_stock_info(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5)
        ttk.Label(card, text="Stock Information", style="Header.TLabel")\
            .pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        box = ttk.Frame(card, style="StockInfo.TFrame"); box.pack(fill=tk.X, padx=12, pady=6)

        self.lbl_company = ttk.Label(box, text="Company (TICKER)", style="StockInfo.TLabel",
                                     font=("Arial",14,"bold"))
        self.lbl_company.pack(anchor=tk.W)
        pf = ttk.Frame(box, style="StockInfo.TFrame"); pf.pack(anchor=tk.W)
        self.lbl_price  = ttk.Label(pf, text="$0.00", style="StockInfo.TLabel",
                                    font=("Arial",20,"bold")); self.lbl_price.pack(side=tk.LEFT)
        self.lbl_change = ttk.Label(pf, text="+0.00 (0.0%)", style="StockInfo.TLabel",
                                    font=("Arial",14)); self.lbl_change.pack(side=tk.LEFT, padx=10)

    def _card_price_chart(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(card, text="Price Chart", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        self.fig, self.ax = plt.subplots(figsize=(6,4), dpi=100)
        self.ax.text(0.5,0.5,"Select a stock", ha="center", va="center")
        self.canvas = FigureCanvasTkAgg(self.fig, master=inner)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _card_candles(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.X, pady=5)
        ttk.Label(card, text="Candlestick", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.X, padx=12, pady=6)
        self.fig2, self.ax2 = plt.subplots(figsize=(6,3), dpi=100)
        self.ax2.text(0.5,0.5,"Select a stock", ha="center", va="center")
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=inner)
        self.canvas2.get_tk_widget().pack(fill=tk.X)

    def _card_hist_table(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(card, text="Historical Data", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        cols = ("Date","Open","High","Low","Close","Volume")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings", height=12)
        for c in cols: self.tree.heading(c,text=c); self.tree.column(c,width=90,anchor=tk.CENTER)
        vsb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _card_recom(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame"); card.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(card, text="Recommendation", style="Header.TLabel").pack(anchor=tk.W, padx=12, pady=(6,3))
        ttk.Separator(card).pack(fill=tk.X, padx=10)
        inner = ttk.Frame(card); inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        self.txt = tk.Text(inner, wrap=tk.WORD, bg=COLORS["bg_medium"], bd=0)
        self.txt.insert(tk.END,"Select a stock to generate recommendation.")
        self.txt.configure(state=tk.DISABLED)
        self.txt.pack(fill=tk.BOTH, expand=True)

    # ========== 视图切换 ==========
    def _show_view(self, key):
        self.current_view = key
        for k,f in self.frames.items():
            f.pack_forget()
        self.frames[key].pack(fill=tk.BOTH, expand=True)
        for k,b in self.nav_buttons.items():
            b.configure(style="Active.Nav.TButton" if k==key else "Nav.TButton")
        if self.current_stock:
            getattr(self, f"_refresh_{key}")()

    def _refresh_overview(self):       self.update_price_chart()
    def _refresh_historical(self):     self._update_candles(); self._update_hist_table()
    def _refresh_recommendation(self): self._update_recom()

    # ========== 数据加载 ==========
    def on_stock_selected(self, *_):
        if self.loading: return
        sel = self.stock_combo.get()
        if not sel: return
        self._show_loading()
        threading.Thread(target=self._load_data, args=(sel,), daemon=True).start()

    def _load_data(self, sel):
        time.sleep(0.05)
        company, ticker = sel.split(" | ")
        df = generate_stock_data(ticker)
        self.stock_data, self.current_stock, self.company_name = df, ticker, company
        self.root.after(0, self._update_all)

    def _update_all(self):
        self._hide_loading()
        self._update_basic_info()
        self._refresh_overview() if self.current_view=="overview" else None
        self._refresh_historical() if self.current_view=="historical" else None
        self._refresh_recommendation() if self.current_view=="recommendation" else None

    # ---------- 状态提示 ----------
    def _show_loading(self):   self.loading=True;  self.loading_lbl.pack()
    def _hide_loading(self):   self.loading=False; self.loading_lbl.pack_forget()

    # ========== 信息/图表/表格/推荐 ==========
    def _update_basic_info(self):
        df = self.stock_data
        last, prev = df.iloc[-1], df.iloc[-2]
        change = last.Close-prev.Close; pct=change/prev.Close*100
        self.lbl_company.config(text=f"{self.company_name} ({self.current_stock})")
        self.lbl_price .config(text=f"${last.Close:.2f}")
        sign_col = COLORS["positive"] if change>=0 else COLORS["negative"]
        self.lbl_change.config(text=f"{change:+.2f} ({pct:+.2f}%)", foreground=sign_col)

    # ----- 价格图 -----
    def update_price_chart(self):
        if self.stock_data is None: return
        df = self.stock_data.iloc[-90:]
        self.ax.clear()
        self.ax.plot(df.index, df.Close, color=COLORS["accent"], lw=2, label="Close")
        if self.ind_vars["sma"].get():  self.ax.plot(df.index, sma(df.Close),  lw=1, ls="--", c="green", label="SMA20")
        if self.ind_vars["ema"].get():  self.ax.plot(df.index, ema(df.Close),  lw=1, ls="--", c="red",   label="EMA20")
        if self.ind_vars["boll"].get():
            m = sma(df.Close); sd=df.Close.rolling(20).std()
            self.ax.fill_between(df.index, m+2*sd, m-2*sd, color="grey", alpha=.15, label="Bollinger")
        if any(v.get() for v in self.ind_vars.values()): self.ax.legend()
        self.ax.set_title(f"{self.current_stock} - Price"); self.ax.grid(alpha=.3)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(self.ax.get_xticklabels(), rotation=45)
        self.fig.tight_layout(); self.canvas.draw()

    # ----- K线 -----
    def _update_candles(self):
        df = self.stock_data.iloc[-30:]
        self.ax2.clear()
        for i,(idx,row) in enumerate(df.iterrows()):
            c = COLORS["positive"] if row.Close>=row.Open else COLORS["negative"]
            self.ax2.plot([idx,idx],[row.Low,row.High],c=c,lw=1)
            self.ax2.bar(idx,row.Close-row.Open,bottom=row.Open,color=c,width=.8,alpha=.7)
        self.ax2.set_title(f"{self.current_stock} - Candlestick")
        self.ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        plt.setp(self.ax2.get_xticklabels(), rotation=45)
        self.fig2.tight_layout(); self.canvas2.draw()

    # ----- 表格 -----
    def _update_hist_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for _,row in self.stock_data.iloc[::-1].head(100).iterrows():
            vals = (row.name.strftime("%Y-%m-%d"),
                    f"${row.Open:.2f}", f"${row.High:.2f}", f"${row.Low:.2f}",
                    f"${row.Close:.2f}", f"{int(row.Volume):,}")
            self.tree.insert("", tk.END, values=vals)

    # ----- 推荐 -----
    def _update_recom(self):
        df = self.stock_data
        cur = df.Close.iloc[-1]; sma20=sma(df.Close).iloc[-1]; r=rsi(df.Close).iloc[-1]
        rec  = "BUY" if cur>sma20 and r<70 else "SELL" if cur<sma20 and r>30 else "HOLD"
        tag  = {"BUY":"positive","SELL":"negative","HOLD":"neutral"}[rec]
        self.txt.config(state=tk.NORMAL); self.txt.delete("1.0",tk.END)
        self.txt.tag_config("positive", foreground=COLORS["positive"])
        self.txt.tag_config("negative", foreground=COLORS["negative"])
        self.txt.tag_config("neutral",  foreground=COLORS["neutral"])
        self.txt.insert(tk.END,f"{self.current_stock} Recommendation\n\n",("header",))
        self.txt.insert(tk.END,f"Current price: ${cur:.2f}\n20-day SMA: ${sma20:.2f}\nRSI(14): {r:.1f}\n\n")
        self.txt.insert(tk.END,f"Suggested action: "); self.txt.insert(tk.END, rec+"\n", (tag,))
        self.txt.config(state=tk.DISABLED)

    # ========== 预加载默认 ==========
    def _preload_default(self):
        def task():
            generate_stock_data(DEFAULT_STOCK)
            self.root.after(200, lambda: (self.stock_combo.current([t for _,t in STOCKS].index(DEFAULT_STOCK)),
                                          self.on_stock_selected()))
        threading.Thread(target=task, daemon=True).start()


# ---------- 启动 ----------
def main():
    root = tk.Tk(); root.title("Financial Data Analytics Software")
    try:
        FinancialAnalyticsApp(root); root.mainloop()
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    main()
