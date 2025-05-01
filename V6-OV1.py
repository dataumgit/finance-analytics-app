import tkinter as tk
from tkinter import ttk, font, messagebox
import numpy as np
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import traceback

# 强制使用 TkAgg 后端（有时在某些环境下需要）
matplotlib.use('TkAgg')

# -----------------------------
# 1. 全局配置和数据缓存
# -----------------------------
COLORS = {
    "bg_dark": "#2C3E50",   # 深灰蓝色背景
    "bg_medium": "#FFFFFF", # 白色背景
    "bg_light": "#F4F6F9",  # 浅灰色背景
    "text": "#333333",      # 深灰色文字
    "accent": "#3498DB",    # 蓝色高亮
    "positive": "#27AE60",  # 绿色
    "negative": "#E74C3C",  # 红色
    "neutral": "#F39C12",   # 橙色
    "header": "#2C3E50",    # 深蓝色标题
    "border": "#BDC3C7",    # 灰色边框
}

STOCK_DATA_CACHE = {}

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
    ("Visa Inc.", "V")
]
DEFAULT_STOCK = "AAPL"

# -----------------------------
# 2. 技术指标计算函数
# -----------------------------
def calculate_sma(data, period=10):
    """计算简单移动平均线(SMA)"""
    return data['Close'].rolling(window=period).mean()

def calculate_ema(data, period=10):
    """计算指数移动平均线(EMA)"""
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    """计算相对强弱指标(RSI)"""
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# -----------------------------
# 3. 数据生成函数
# -----------------------------
def generate_stock_data(ticker, days=180):
    """生成模拟股票数据，并使用缓存避免重复生成"""
    try:
        if ticker in STOCK_DATA_CACHE:
            return STOCK_DATA_CACHE[ticker]

        np.random.seed(hash(ticker) % 100)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start_date, end_date)

        # 随机初始价格
        start_price = np.random.randint(50, 500)

        # 随机波动 + 趋势
        price_changes = np.random.normal(0, 0.015, len(date_range))
        trend = (hash(ticker) % 7 - 3) / 100  # -0.03 ~ 0.03
        price_changes += trend

        prices = start_price * (1 + price_changes).cumprod()

        data = pd.DataFrame(index=date_range)
        data['Date'] = date_range
        data['Close'] = prices

        daily_volatility = prices * np.random.uniform(0.005, 0.02, len(prices))
        data['Open'] = prices * (1 + np.random.uniform(-0.01, 0.01, len(prices)))
        data['High'] = np.maximum(data['Open'], data['Close']) + daily_volatility
        data['Low'] = np.minimum(data['Open'], data['Close']) - daily_volatility

        # 确保High/Low正确
        data['High'] = np.maximum(data['High'], np.maximum(data['Open'], data['Close']))
        data['Low'] = np.minimum(data['Low'], np.minimum(data['Open'], data['Close']))

        data['Volume'] = np.random.randint(100, 10000, len(date_range))

        # 缓存结果
        STOCK_DATA_CACHE[ticker] = data
        return data

    except Exception as e:
        print(f"Error generating stock data: {e}")
        empty_data = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        return empty_data

# -----------------------------
# 4. 自定义CheckmarkButton类
# -----------------------------
class CheckmarkButton(ttk.Frame):
    """带自定义勾选框的复选按钮"""
    def __init__(self, master=None, text="", variable=None, command=None):
        super().__init__(master)
        self.configure(style="TFrame")

        self.variable = variable
        self.command = command
        self.text = text

        # 勾选框使用普通的Label来模拟
        self.check_label = tk.Label(self, text=" ", width=2, relief="solid", borderwidth=1, bg="white", font=('Arial', 10))
        self.check_label.pack(side=tk.LEFT, padx=(0, 5))

        self.text_label = ttk.Label(self, text=text)
        self.text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 绑定点击事件
        self.check_label.bind("<Button-1>", self.toggle)
        self.text_label.bind("<Button-1>", self.toggle)
        self.bind("<Button-1>", self.toggle)

        # 初始化显示
        self.update_checkmark()

        # 监听variable变化
        if self.variable:
            self.variable.trace_add("write", self.update_checkmark)

    def toggle(self, event=None):
        if self.variable:
            self.variable.set(not self.variable.get())
            if self.command:
                self.command()

    def update_checkmark(self, *args):
        if self.variable and self.variable.get():
            self.check_label.configure(text="√", bg="#DFF0D8", borderwidth=2, relief="solid")
        else:
            self.check_label.configure(text=" ", bg="white", borderwidth=1, relief="solid")

# -----------------------------
# 5. 主应用类
# -----------------------------
class FinancialAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Data Analytics Software")
        self.root.geometry("1280x720")
        self.root.configure(bg=COLORS["bg_dark"])

        # 关键成员变量
        self.current_stock = None
        self.stock_data = None
        self.loading = False
        self.current_view = "overview"

        # UI元素的引用
        self.stock_info = {}       # 用于存放股票信息相关的Label
        self.indicators = {}       # 用于存放技术指标复选框
        self.nav_buttons = {}      # 用于导航按钮
        self.content_frames = {}   # 用于切换不同视图
        self.canvas = None         # 价格图
        self.ax = None
        self.fig = None
        self.hist_canvas = None    # K线图
        self.hist_ax = None
        self.hist_fig = None
        self.hist_tree = None      # 历史数据表格
        self.rec_text = None       # 推荐内容

        # 初始化
        self.setup_fonts()
        self.setup_styles()
        self.create_ui()

        # 预加载默认股票数据
        self.preload_default_stock()

    # 5.1 字体设置
    def setup_fonts(self):
        self.title_font = font.Font(family="Arial", size=14, weight="bold")
        self.header_font = font.Font(family="Arial", size=12, weight="bold")
        self.normal_font = font.Font(family="Arial", size=10)

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Arial", size=10)

    # 5.2 ttk风格设置
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # 一些自定义风格
        self.style.configure("TFrame", background=COLORS["bg_medium"])
        self.style.configure("Card.TFrame", background=COLORS["bg_medium"], relief="raised")
        self.style.configure("StockInfo.TFrame", background="#2C3E50")
        self.style.configure("StockInfo.TLabel", background="#2C3E50", foreground="white")

        # 标题style示例
        self.style.configure("Title.TLabel", font=self.title_font, background=COLORS["bg_medium"], foreground=COLORS["text"])
        self.style.configure("Header.TLabel", font=self.header_font, background=COLORS["bg_medium"], foreground=COLORS["text"])

        # 导航按钮style
        self.style.configure("Nav.TButton", background=COLORS["bg_light"], font=("Arial", 10))
        self.style.map("Nav.TButton", background=[("active", COLORS["bg_light"])])

        # 激活导航按钮的style
        self.style.configure("Active.Nav.TButton", background=COLORS["accent"], foreground="#ffffff")

    # 5.3 创建主UI
    def create_ui(self):
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部标题区域
        title_frame = ttk.Frame(main_frame, style="TFrame")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="Financial Data Analytics", style="Title.TLabel").pack(side=tk.LEFT)

        # 内容区域：左右布局
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧面板
        left_frame = ttk.Frame(content_frame, style="TFrame", width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # 创建左侧UI组件
        self.create_stock_selection_card(left_frame)
        self.create_indicators_card(left_frame)
        self.create_navigation_card(left_frame)

        # 右侧面板
        self.right_frame = ttk.Frame(content_frame, style="TFrame")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建各个“视图”容器
        self.content_frames["overview"] = ttk.Frame(self.right_frame, style="TFrame")
        self.create_stock_info_card(self.content_frames["overview"])
        self.create_price_chart_card(self.content_frames["overview"])

        self.content_frames["historical"] = ttk.Frame(self.right_frame, style="TFrame")
        self.create_historical_chart_card(self.content_frames["historical"])
        self.create_historical_data_card(self.content_frames["historical"])

        self.content_frames["recommendation"] = ttk.Frame(self.right_frame, style="TFrame")
        self.create_recommendation_card(self.content_frames["recommendation"])

        # 默认显示overview视图
        self.show_section("overview")

    # 5.3.1 股票选择卡片
    def create_stock_selection_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        ttk.Label(card, text="Stock Selection", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15)

        ttk.Label(content, text="Select Stock:").pack(anchor=tk.W, pady=(0, 5))

        # 下拉框选择股票
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(content, textvariable=self.stock_var, state="readonly", width=30)
        stock_options = [f"{name} | {ticker}" for name, ticker in STOCKS]
        self.stock_combo['values'] = stock_options
        self.stock_combo.pack(fill=tk.X)

        # 当选择股票时触发
        self.stock_combo.bind("<<ComboboxSelected>>", self.on_stock_selected)

        # “加载中”提示
        self.loading_frame = ttk.Frame(content, style="TFrame")
        self.loading_frame.pack(fill=tk.X, pady=5)
        self.loading_label = ttk.Label(self.loading_frame, text="Loading data...", style="TLabel")
        self.loading_label.pack(anchor=tk.W)
        self.loading_frame.pack_forget()

    # 5.3.2 技术指标卡片
    def create_indicators_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        ttk.Label(card, text="Technical Indicators", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15)

        # 指标选项
        self.indicators = {
            "sma": {"var": tk.BooleanVar(value=False), "name": "Simple Moving Average (SMA)"},
            "ema": {"var": tk.BooleanVar(value=False), "name": "Exponential Moving Average (EMA)"},
            "bollinger": {"var": tk.BooleanVar(value=False), "name": "Bollinger Bands"},
            "rsi": {"var": tk.BooleanVar(value=False), "name": "Relative Strength Index (RSI)"},
        }

        for key, ind in self.indicators.items():
            cb = CheckmarkButton(content, text=ind["name"], variable=ind["var"], command=self.update_indicators)
            cb.pack(anchor=tk.W, pady=3, fill=tk.X)

    # 5.3.3 导航卡片
    def create_navigation_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        ttk.Label(card, text="Navigation", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15)

        nav_options = [
            ("overview", "Overview"),
            ("historical", "Historical Data"),
            ("recommendation", "Investment Recommendation")
        ]
        for key, text in nav_options:
            btn = ttk.Button(content, text=text, style="Nav.TButton",
                             command=lambda k=key: self.show_section(k))
            btn.pack(fill=tk.X, pady=3, ipady=5)
            self.nav_buttons[key] = btn

        # 默认显示“overview”
        self.nav_buttons["overview"].configure(style="Active.Nav.TButton")

    # 5.3.4 股票信息卡片
    def create_stock_info_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        ttk.Label(card, text="Stock Information", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="StockInfo.TFrame")
        content.pack(fill=tk.X, padx=15, pady=10)

        # 顶部公司信息
        company_frame = ttk.Frame(content, style="StockInfo.TFrame")
        company_frame.pack(fill=tk.X, pady=5)

        self.stock_info["company"] = ttk.Label(company_frame, text="Company Name (TICKER)",
                                               font=('Arial', 16, 'bold'),
                                               style="StockInfo.TLabel")
        self.stock_info["company"].pack(side=tk.LEFT)

        # 价格+涨跌
        price_frame = ttk.Frame(content, style="StockInfo.TFrame")
        price_frame.pack(fill=tk.X, pady=10)

        self.stock_info["price"] = ttk.Label(price_frame, text="$0.00",
                                             font=('Arial', 20, 'bold'),
                                             style="StockInfo.TLabel")
        self.stock_info["price"].pack(side=tk.LEFT)

        self.stock_info["change"] = ttk.Label(price_frame, text="+0.00 (+0.00%)",
                                              font=('Arial', 14, 'bold'),
                                              width=20, anchor=tk.W,
                                              style="StockInfo.TLabel")
        self.stock_info["change"].pack(side=tk.LEFT, padx=(10, 0))

        # Open/High/Low/Volume
        data_frame = ttk.Frame(content, style="StockInfo.TFrame")
        data_frame.pack(fill=tk.X, pady=5)

        for label_text in ["Open:", "Day High:", "Day Low:", "Volume:"]:
            sub_frame = ttk.Frame(data_frame, style="StockInfo.TFrame")
            sub_frame.pack(side=tk.LEFT, padx=10)

            ttk.Label(sub_frame, text=label_text, font=('Arial', 10, 'bold'), style="StockInfo.TLabel").pack(anchor=tk.W)
            key = label_text.lower().replace(" ", "").replace(":", "")
            self.stock_info[key] = ttk.Label(sub_frame, text="--", font=('Arial', 12), style="StockInfo.TLabel")
            self.stock_info[key].pack(anchor=tk.W)

    # 5.3.5 价格图卡片
    def create_price_chart_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        ttk.Label(card, text="Price Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor(COLORS["bg_medium"])
        self.ax.set_facecolor(COLORS["bg_medium"])

        self.ax.text(0.5, 0.5, "Select a stock to view data",
                     horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes, fontsize=14, color=COLORS["text"])
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.canvas = FigureCanvasTkAgg(self.fig, master=content)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # 5.3.6 历史K线图卡片
    def create_historical_chart_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        ttk.Label(card, text="Candlestick Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.hist_fig, self.hist_ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.hist_fig.patch.set_facecolor(COLORS["bg_medium"])
        self.hist_ax.set_facecolor(COLORS["bg_medium"])

        self.hist_ax.text(0.5, 0.5, "Select a stock to view historical data",
                          horizontalalignment='center', verticalalignment='center',
                          transform=self.hist_ax.transAxes, fontsize=14, color=COLORS["text"])
        self.hist_ax.set_xticks([])
        self.hist_ax.set_yticks([])

        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=content)
        self.hist_canvas.get_tk_widget().config(height=300)
        self.hist_canvas.get_tk_widget().pack(fill=tk.X)

    # 5.3.7 历史数据表格卡片
    def create_historical_data_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        ttk.Label(card, text="Historical Data", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        columns = ("Date", "Open", "High", "Low", "Close", "Volume")
        self.hist_tree = ttk.Treeview(content, columns=columns, show="headings", height=10)

        for col in columns:
            self.hist_tree.heading(col, text=col)
            self.hist_tree.column(col, width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=scrollbar.set)

        self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 5.3.8 投资推荐卡片
    def create_recommendation_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        ttk.Label(card, text="Investment Recommendation", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.rec_text = tk.Text(content, wrap=tk.WORD, bg=COLORS["bg_medium"], fg=COLORS["text"],
                                bd=0, padx=5, pady=5, font=self.normal_font)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.rec_text.yview)
        self.rec_text.configure(yscrollcommand=scrollbar.set)

        self.rec_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.rec_text.config(state=tk.NORMAL)
        self.rec_text.insert(tk.END, "Select a stock to view investment recommendations.")
        self.rec_text.config(state=tk.DISABLED)

    # -----------------------------
    # 6. 预加载默认股票
    # -----------------------------
    def preload_default_stock(self):
        """后台线程预先加载默认股票数据"""
        threading.Thread(target=self._preload_stock_data, daemon=True).start()

    def _preload_stock_data(self):
        try:
            generate_stock_data(DEFAULT_STOCK)
            self.root.after(500, self.set_default_stock)
        except Exception as e:
            print(f"Error preloading stock data: {e}")
            traceback.print_exc()

    def set_default_stock(self):
        """在下拉框中选中默认股票并触发加载"""
        for i, (name, ticker) in enumerate(STOCKS):
            if ticker == DEFAULT_STOCK:
                self.stock_combo.current(i)
                self.on_stock_selected(None)
                break

    # -----------------------------
    # 7. 事件处理 / UI更新
    # -----------------------------
    def on_stock_selected(self, event):
        """
        当用户在下拉框中选择股票时触发。
        如果没有此方法，会报 AttributeError: 'FinancialAnalyticsApp' object has no attribute 'on_stock_selected'。
        """
        if self.loading:
            return

        selected = self.stock_combo.get()
        if not selected:
            return

        # 显示“加载中”提示
        self.show_loading()

        # 后台线程加载数据
        threading.Thread(target=self.load_stock_data, args=(selected,), daemon=True).start()

    def load_stock_data(self, selected):
        """后台加载股票数据"""
        try:
            time.sleep(0.1)
            company, ticker = selected.split(" | ")
            self.current_stock = ticker
            self.stock_data = generate_stock_data(ticker)

            # 在主线程中更新UI
            self.root.after(0, lambda: self.update_ui(company, ticker))
        except Exception as e:
            print(f"Error loading stock data: {e}")
            traceback.print_exc()
            self.root.after(0, self.hide_loading)

    def show_loading(self):
        """显示'加载中'提示"""
        self.loading = True
        self.loading_frame.pack(fill=tk.X, pady=5)
        self.root.update_idletasks()

    def hide_loading(self):
        """隐藏'加载中'提示"""
        self.loading = False
        self.loading_frame.pack_forget()
        self.root.update_idletasks()

    def update_ui(self, company, ticker):
        """在主线程中更新UI"""
        try:
            self.update_stock_info(company, ticker)

            # 根据当前视图更新内容
            if self.current_view == "overview":
                self.update_price_chart()
            elif self.current_view == "historical":
                self.update_historical_data()
            elif self.current_view == "recommendation":
                self.update_recommendation()
        finally:
            self.hide_loading()

    # 7.1 更新股票信息
    def update_stock_info(self, company, ticker):
        if self.stock_data is None or len(self.stock_data) < 2:
            return

        latest = self.stock_data.iloc[-1]
        prev = self.stock_data.iloc[-2]

        price_change = latest['Close'] - prev['Close']
        price_change_pct = (price_change / prev['Close']) * 100

        self.stock_info["company"].config(text=f"{company} ({ticker})")
        self.stock_info["price"].config(text=f"${latest['Close']:.2f}")
        change_text = f"{price_change:+.2f} ({price_change_pct:+.2f}%)"

        if price_change >= 0:
            self.stock_info["change"].config(text=change_text, foreground="green", background="#DFF0D8")
        else:
            self.stock_info["change"].config(text=change_text, foreground="red", background="#F2DEDE")

        self.stock_info["open"].config(text=f"${latest['Open']:.2f}")
        self.stock_info["dayhigh"].config(text=f"${latest['High']:.2f}")
        self.stock_info["daylow"].config(text=f"${latest['Low']:.2f}")
        self.stock_info["volume"].config(text=f"{latest['Volume']:,}")

    # 7.2 更新技术指标
    def update_indicators(self):
        """当技术指标复选框被切换时触发"""
        if self.current_stock:
            if self.current_view == "overview":
                self.update_price_chart()

    # 7.3 显示不同的视图
    def show_section(self, section):
        self.current_view = section

        # 导航按钮样式切换
        for key, btn in self.nav_buttons.items():
            if key == section:
                btn.configure(style="Active.Nav.TButton")
            else:
                btn.configure(style="Nav.TButton")

        # 隐藏所有frame
        for frame in self.content_frames.values():
            frame.pack_forget()

        # 显示当前frame
        self.content_frames[section].pack(fill=tk.BOTH, expand=True)

        # 更新显示
        if self.current_stock:
            if section == "overview":
                self.update_price_chart()
            elif section == "historical":
                self.update_historical_data()
            elif section == "recommendation":
                self.update_recommendation()

    # 7.4 更新价格图
    def update_price_chart(self):
        if self.stock_data is None or len(self.stock_data) < 1:
            return

        self.ax.clear()
        days = min(90, len(self.stock_data))
        data = self.stock_data.iloc[-days:]

        self.ax.plot(data.index, data['Close'], color=COLORS["accent"], linewidth=2, label='Price')
        self.add_indicators_to_chart(data)

        self.ax.set_title(f"{self.current_stock} - Price Chart", color=COLORS["header"])
        self.ax.set_xlabel('Date', color=COLORS["text"])
        self.ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["border"])

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)

        if any(indicator["var"].get() for indicator in self.indicators.values()):
            self.ax.legend(loc='upper left')

        self.canvas.draw()

    # 7.5 在图表上添加技术指标
    def add_indicators_to_chart(self, data):
        for key, indicator in self.indicators.items():
            if not indicator["var"].get():
                continue

            if key == "sma":
                sma = calculate_sma(data, period=20)
                self.ax.plot(data.index, sma, color='green', linestyle='--', linewidth=1.5, label='SMA (20)')

            elif key == "ema":
                ema = calculate_ema(data, period=20)
                self.ax.plot(data.index, ema, color='red', linestyle='--', linewidth=1.5, label='EMA (20)')

            elif key == "bollinger":
                try:
                    sma = calculate_sma(data, period=20)
                    std = data['Close'].rolling(window=20).std()
                    upper_band = sma + (std * 2)
                    lower_band = sma - (std * 2)
                    self.ax.plot(data.index, upper_band, color='green', linestyle='-', linewidth=1, alpha=0.5, label='Upper BB')
                    self.ax.plot(data.index, sma, color='orange', linestyle='-', linewidth=1, alpha=0.5, label='Middle BB')
                    self.ax.plot(data.index, lower_band, color='red', linestyle='-', linewidth=1, alpha=0.5, label='Lower BB')
                    self.ax.fill_between(data.index, upper_band, lower_band, alpha=0.1, color='gray')
                except Exception as e:
                    print(f"Error calculating Bollinger Bands: {e}")

            elif key == "rsi":
                try:
                    if len(data) > 14:
                        rsi_val = calculate_rsi(data)
                        ax2 = self.ax.twinx()
                        ax2.set_ylabel('RSI', color='orange')
                        ax2.plot(data.index, rsi_val, color='orange', linewidth=1.5, label='RSI (14)')
                        ax2.set_ylim([0, 100])
                        ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5)
                        ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5)
                except Exception as e:
                    print(f"Error calculating RSI: {e}")

    # 7.6 更新历史数据视图
    def update_historical_data(self):
        if self.stock_data is None or len(self.stock_data) < 1:
            return

        self.update_candlestick_chart()
        self.update_historical_table()

    # 7.6.1 更新K线图
    def update_candlestick_chart(self):
        self.hist_ax.clear()

        days = min(30, len(self.stock_data))
        data = self.stock_data.iloc[-days:]

        for i in range(len(data)):
            date = data.index[i]
            open_price = data['Open'].iloc[i]
            close_price = data['Close'].iloc[i]
            high_price = data['High'].iloc[i]
            low_price = data['Low'].iloc[i]

            color = COLORS["positive"] if close_price >= open_price else COLORS["negative"]
            self.hist_ax.plot([date, date], [low_price, high_price], color=color, linewidth=1)
            self.hist_ax.bar(date, close_price - open_price, bottom=open_price, color=color, width=0.8, alpha=0.6)

        self.hist_ax.set_title(f"{self.current_stock} - Candlestick Chart", color=COLORS["header"])
        self.hist_ax.set_xlabel('Date', color=COLORS["text"])
        self.hist_ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.hist_ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["border"])

        self.hist_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.hist_ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(self.hist_ax.xaxis.get_majorticklabels(), rotation=45)

        self.hist_canvas.draw()

    # 7.6.2 更新历史数据表格
    def update_historical_table(self):
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        num_rows = min(100, len(self.stock_data))
        for i in range(num_rows):
            idx = len(self.stock_data) - 1 - i
            row = self.stock_data.iloc[idx]
            date_str = row.name.strftime('%Y-%m-%d')

            open_price = f"${row['Open']:.2f}"
            high_price = f"${row['High']:.2f}"
            low_price = f"${row['Low']:.2f}"
            close_price = f"${row['Close']:.2f}"
            volume = f"{row['Volume']:,}"

            self.hist_tree.insert("", tk.END, values=(date_str, open_price, high_price, low_price, close_price, volume))

    # 7.7 更新投资推荐
    def update_recommendation(self):
        # ... 此处保留原有的推荐逻辑 ...
        pass

def main():
    root = tk.Tk()
    app = FinancialAnalyticsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
