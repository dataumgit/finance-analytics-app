import tkinter as tk
from tkinter import ttk, font
import numpy as np
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import traceback
import time
import matplotlib.pyplot as plt
import self
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('TkAgg')  # 强制使用 TkAgg 后端

# Define color scheme for financial app
# COLORS = {
#     "bg_dark": "#E8EEF4",  # Light blue-gray background
#     "bg_medium": "#FFFFFF",  # White for panels
#     "bg_light": "#FFFFFF",  # White for inputs
#     "text": "#333333",  # Dark gray text
#     "accent": "#3498DB",  # Blue accent for buttons
#     "positive": "#27AE60",  # Green for positive values
#     "negative": "#E74C3C",  # Red for negative values
#     "neutral": "#F39C12",  # Orange for neutral/warning
#     "header": "#2C3E50",  # Dark blue for headers
#     "border": "#BDC3C7",  # Light gray for borders
# }

COLORS = {
    "bg_dark": "#2C3E50",  # 深灰蓝色背景
    "bg_medium": "#FFFFFF",  # 白色背景
    "bg_light": "#F4F6F9",  # 浅灰色背景
    "text": "#333333",  # 深灰色文字
    "accent": "#3498DB",  # 蓝色高亮
    "positive": "#27AE60",  # 绿色
    "negative": "#E74C3C",  # 红色
    "neutral": "#F39C12",  # 橙色
    "header": "#2C3E50",  # 深蓝色标题
    "border": "#BDC3C7",  # 灰色边框
}

# Stock data cache to improve performance
STOCK_DATA_CACHE = {}

# Sample stock list (company name and ticker)
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

# Default stock to show on startup
DEFAULT_STOCK = "AAPL"


# Generate simulated stock data with error handling
def generate_stock_data(ticker, days=180):
    try:
        # Check cache first
        if ticker in STOCK_DATA_CACHE:
            return STOCK_DATA_CACHE[ticker]

        # Set seed for reproducibility
        np.random.seed(hash(ticker) % 100)

        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start_date, end_date)

        # Starting price between 50 and 500
        start_price = np.random.randint(50, 500)

        # Generate price movements
        price_changes = np.random.normal(0, 0.015, len(date_range))
        trend = (hash(ticker) % 7 - 3) / 100  # Between -0.03 and 0.03
        price_changes += trend

        # Calculate prices
        prices = start_price * (1 + price_changes).cumprod()

        # Create dataframe
        data = pd.DataFrame(index=date_range)
        data['Date'] = date_range
        data['Close'] = prices

        # Generate OHLC data
        daily_volatility = prices * np.random.uniform(0.005, 0.02, len(prices))
        data['Open'] = prices * (1 + np.random.uniform(-0.01, 0.01, len(prices)))
        data['High'] = np.maximum(data['Open'], data['Close']) + daily_volatility
        data['Low'] = np.minimum(data['Open'], data['Close']) - daily_volatility

        # Ensure High >= Open, Close and Low <= Open, Close
        data['High'] = np.maximum(data['High'], np.maximum(data['Open'], data['Close']))
        data['Low'] = np.minimum(data['Low'], np.minimum(data['Open'], data['Close']))

        # Generate volume
        data['Volume'] = np.random.randint(100, 10000, len(date_range))

        # Store in cache
        STOCK_DATA_CACHE[ticker] = data

        return data
    except Exception as e:
        print(f"Error generating stock data: {e}")
        # Return empty dataframe with same structure in case of error
        empty_data = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        return empty_data


# Technical indicators
def calculate_sma(data, period=10):
    """Calculate Simple Moving Average"""
    return data['Close'].rolling(window=period).mean()


def calculate_ema(data, period=10):
    """Calculate Exponential Moving Average"""
    return data['Close'].ewm(span=period, adjust=False).mean()


def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index"""
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Custom Checkmark Button class
class CheckmarkButton(ttk.Frame):
    def __init__(self, master=None, text="", variable=None, command=None):
        super().__init__(master)
        self.configure(style="TFrame")

        self.variable = variable
        self.command = command
        self.text = text

        # 更改为标准Label以便自定义边框
        self.check_label = tk.Label(self, text=" ", width=2, relief="solid", borderwidth=1, bg="white", font=('Arial', 10))
        self.check_label.pack(side=tk.LEFT, padx=(0, 5))

        self.text_label = ttk.Label(self, text=text)
        self.text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Bind events
        self.check_label.bind("<Button-1>", self.toggle)
        self.text_label.bind("<Button-1>", self.toggle)
        self.bind("<Button-1>", self.toggle)

        # Set initial state
        self.update_checkmark()

        # Trace variable changes
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


class FinancialAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Data Analytics Software")
        self.root.geometry("1280x720")
        self.root.configure(bg=COLORS["bg_dark"])

        # Initialize variables
        self.current_stock = None
        self.stock_data = None
        self.loading = False

        # Create fonts
        self.title_font = font.Font(family="Arial", size=14, weight="bold")
        self.header_font = font.Font(family="Arial", size=12, weight="bold")
        self.normal_font = font.Font(family="Arial", size=10)

        # Set default font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Arial", size=10)

        # Configure styles
        self.setup_styles()

        # Create UI
        self.create_ui()

        # Preload default stock data
        self.preload_default_stock()

    def setup_styles(self):
        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Define custom style for the frames and labels
        self.style.configure("TFrame", background=COLORS["bg_medium"])
        self.style.configure("Card.TFrame", background=COLORS["bg_medium"], relief="raised")

        # Custom background color for the stock info section
        self.style.configure("StockInfo.TFrame", background="#2C3E50")  # 浅黑色背景
        self.style.configure("StockInfo.TLabel", background="#2C3E50", foreground="white")  # 白色文本


    def create_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, style="App.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # App title
        title_frame = ttk.Frame(main_frame, style="App.TFrame")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="Financial Data Analytics", style="Title.TLabel").pack(side=tk.LEFT)

        # Content frame (contains left and right panels)
        content_frame = ttk.Frame(main_frame, style="App.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel
        left_frame = ttk.Frame(content_frame, style="App.TFrame", width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)  # Prevent shrinking

        # Create cards for left panel
        self.create_stock_selection_card(left_frame)
        self.create_indicators_card(left_frame)
        self.create_navigation_card(left_frame)

        # Right panel
        self.right_frame = ttk.Frame(content_frame, style="App.TFrame")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Content frames
        self.content_frames = {}

        # Overview frame
        self.content_frames["overview"] = ttk.Frame(self.right_frame, style="App.TFrame")
        self.create_stock_info_card(self.content_frames["overview"])
        self.create_price_chart_card(self.content_frames["overview"])

        # Historical data frame
        self.content_frames["historical"] = ttk.Frame(self.right_frame, style="App.TFrame")
        self.create_historical_chart_card(self.content_frames["historical"])
        self.create_historical_data_card(self.content_frames["historical"])

        # Recommendation frame
        self.content_frames["recommendation"] = ttk.Frame(self.right_frame, style="App.TFrame")
        self.create_recommendation_card(self.content_frames["recommendation"])

        # Show default section
        self.show_section("overview")

    def create_stock_selection_card(self, parent):
        # Stock selection card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Stock Selection", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Stock selection content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15)

        ttk.Label(content, text="Select Stock:").pack(anchor=tk.W, pady=(0, 5))

        # Combobox for stock selection
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(content, textvariable=self.stock_var, state="readonly", width=30)
        stock_options = [f"{name} | {ticker}" for name, ticker in STOCKS]
        self.stock_combo['values'] = stock_options
        self.stock_combo.pack(fill=tk.X)
        self.stock_combo.bind("<<ComboboxSelected>>", self.on_stock_selected)

        # Loading indicator
        self.loading_frame = ttk.Frame(content, style="TFrame")
        self.loading_frame.pack(fill=tk.X, pady=5)
        self.loading_label = ttk.Label(self.loading_frame, text="Loading data...", style="TLabel")
        self.loading_label.pack(anchor=tk.W)
        self.loading_frame.pack_forget()  # Hide initially

    def create_indicators_card(self, parent):
        # Technical indicators card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Technical Indicators", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Indicators content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15)

        # Checkboxes for technical indicators
        self.indicators = {
            "sma": {"var": tk.BooleanVar(), "name": "Simple Moving Average (SMA)"},
            "ema": {"var": tk.BooleanVar(), "name": "Exponential Moving Average (EMA)"},
            "bollinger": {"var": tk.BooleanVar(), "name": "Bollinger Bands"},
            "rsi": {"var": tk.BooleanVar(), "name": "Relative Strength Index (RSI)"},
            "macd": {"var": tk.BooleanVar(), "name": "MACD"},
            "atr": {"var": tk.BooleanVar(), "name": "Average True Range (ATR)"}
        }

        # Create custom checkmark buttons
        for key, indicator in self.indicators.items():
            cb = CheckmarkButton(
                content,
                text=indicator["name"],
                variable=indicator["var"],
                command=self.update_indicators
            )
            cb.pack(anchor=tk.W, pady=3, fill=tk.X)



    def create_navigation_card(self, parent):
        # Navigation card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Navigation", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Navigation content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15)

        # Navigation buttons
        self.nav_buttons = {}
        nav_options = [
            ("overview", "Overview"),
            ("historical", "Historical Data"),
            ("recommendation", "Investment Recommendation")
        ]

        for key, text in nav_options:
            btn = ttk.Button(
                content,
                text=text,
                command=lambda k=key: self.show_section(k),
                style="Nav.TButton"
            )
            btn.pack(fill=tk.X, pady=3, ipady=5)
            self.nav_buttons[key] = btn

        # Set active button
        self.nav_buttons["overview"].configure(style="Active.Nav.TButton")

    def create_stock_info_card(self, parent):
        # Stock info card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Stock Information", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Stock info content using the custom style
        content = ttk.Frame(card, style="StockInfo.TFrame")
        content.pack(fill=tk.X, padx=15, pady=10)

        # Company and Ticker on top
        company_frame = ttk.Frame(content, style="StockInfo.TFrame")
        company_frame.pack(fill=tk.X, pady=5)

        self.stock_info = {}
        self.stock_info["company"] = ttk.Label(company_frame, text="Company Name (TICKER)", font=('Arial', 16, 'bold'),
                                               style="StockInfo.TLabel")
        self.stock_info["company"].pack(side=tk.LEFT)

        # Price and Change with updated background
        price_frame = ttk.Frame(content, style="StockInfo.TFrame")
        price_frame.pack(fill=tk.X, pady=10)

        self.stock_info["price"] = ttk.Label(price_frame, text="$0.00", font=('Arial', 20, 'bold'),
                                             style="StockInfo.TLabel")
        self.stock_info["price"].pack(side=tk.LEFT)

        self.stock_info["change"] = ttk.Label(price_frame, text="+0.00 (+0.00%)", font=('Arial', 14, 'bold'), width=20,
                                              anchor=tk.W, style="StockInfo.TLabel")
        self.stock_info["change"].pack(side=tk.LEFT, padx=(10, 0))

        # Additional data (Open, High, Low, Volume)
        data_frame = ttk.Frame(content, style="StockInfo.TFrame")
        data_frame.pack(fill=tk.X, pady=5)

        for label_text in ["Open:", "Day High:", "Day Low:", "Volume:"]:
            sub_frame = ttk.Frame(data_frame, style="StockInfo.TFrame")
            sub_frame.pack(side=tk.LEFT, padx=10)

            ttk.Label(sub_frame, text=label_text, font=('Arial', 10, 'bold'), style="StockInfo.TLabel").pack(
                anchor=tk.W)
            key = label_text.lower().replace(" ", "").replace(":", "")
            self.stock_info[key] = ttk.Label(sub_frame, text="--", font=('Arial', 12), style="StockInfo.TLabel")
            self.stock_info[key].pack(anchor=tk.W)

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import tkinter as tk

    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import tkinter as tk
    from tkinter import ttk

    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import tkinter as tk
    from tkinter import ttk

    def create_price_chart_card(self, parent):
        # Chart card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Price Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Chart content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Create matplotlib figure for chart
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor(COLORS["bg_medium"])
        self.ax.set_facecolor(COLORS["bg_medium"])

        # Set up placeholder text
        self.ax.text(0.5, 0.5, "Select a stock to view data",
                     horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes, fontsize=14, color=COLORS["text"])
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=content)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_zoom(self, event):
        """Zoom in/out on mouse scroll"""
        base_scale = 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata

        if event.button == 'up':
            # Zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            # Zoom out
            scale_factor = base_scale
        else:
            scale_factor = 1

        self.ax.set_xlim([xdata - (xdata - cur_xlim[0]) * scale_factor, xdata + (cur_xlim[1] - xdata) * scale_factor])
        self.ax.set_ylim([ydata - (ydata - cur_ylim[0]) * scale_factor, ydata + (cur_ylim[1] - ydata) * scale_factor])

        self.fig.canvas.draw()

    def create_historical_chart_card(self, parent):
        # Historical chart card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Candlestick Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Chart content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Create matplotlib figure for historical chart
        self.hist_fig, self.hist_ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.hist_fig.patch.set_facecolor(COLORS["bg_medium"])
        self.hist_ax.set_facecolor(COLORS["bg_medium"])

        # Set up placeholder text
        self.hist_ax.text(0.5, 0.5, "Select a stock to view historical data",
                          horizontalalignment='center', verticalalignment='center',
                          transform=self.hist_ax.transAxes, fontsize=14, color=COLORS["text"])
        self.hist_ax.set_xticks([])
        self.hist_ax.set_yticks([])

        # Create canvas with fixed height
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=content)
        canvas_widget = self.hist_canvas.get_tk_widget()
        canvas_widget.config(height=300)
        canvas_widget.pack(fill=tk.X)

    def create_historical_data_card(self, parent):
        # Historical data table card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Historical Data", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Table content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Create treeview for historical data
        columns = ("Date", "Open", "High", "Low", "Close", "Volume")
        self.hist_tree = ttk.Treeview(content, columns=columns, show="headings", height=10)

        # Set column headings
        for col in columns:
            self.hist_tree.heading(col, text=col)
            self.hist_tree.column(col, width=100, anchor=tk.CENTER)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_recommendation_card(self, parent):
        # Recommendation card
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        # Card title
        ttk.Label(card, text="Investment Recommendation", style="Header.TLabel").pack(anchor=tk.W, padx=15,
                                                                                      pady=(10, 5))
        ttk.Separator(card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 10))

        # Recommendation content
        content = ttk.Frame(card, style="TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Create text widget
        self.rec_text = tk.Text(content, wrap=tk.WORD, bg=COLORS["bg_medium"], fg=COLORS["text"],
                                bd=0, padx=5, pady=5, font=self.normal_font)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.rec_text.yview)
        self.rec_text.configure(yscrollcommand=scrollbar.set)

        self.rec_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Set read-only
        self.rec_text.config(state=tk.DISABLED)

        # Configure text tags
        self.rec_text.tag_configure("title", font=self.title_font, foreground=COLORS["header"])
        self.rec_text.tag_configure("header", font=self.header_font, foreground=COLORS["header"])
        self.rec_text.tag_configure("positive", foreground=COLORS["positive"])
        self.rec_text.tag_configure("negative", foreground=COLORS["negative"])
        self.rec_text.tag_configure("neutral", foreground=COLORS["neutral"])

        # Set placeholder text
        self.rec_text.config(state=tk.NORMAL)
        self.rec_text.insert(tk.END, "Select a stock to view investment recommendations.")
        self.rec_text.config(state=tk.DISABLED)

    def preload_default_stock(self):
        """Preload default stock in a separate thread to avoid freezing UI"""
        threading.Thread(target=self._preload_stock_data, daemon=True).start()

    def _preload_stock_data(self):
        """Background task to preload stock data"""
        try:
            # Generate data for default stock
            generate_stock_data(DEFAULT_STOCK)

            # Set the default stock in the UI
            self.root.after(500, self.set_default_stock)
        except Exception as e:
            print(f"Error preloading stock data: {e}")
            traceback.print_exc()

    def set_default_stock(self):
        """Set the default stock in the UI"""
        # Find the stock option with the default ticker
        for i, (name, ticker) in enumerate(STOCKS):
            if ticker == DEFAULT_STOCK:
                self.stock_combo.current(i)
                self.on_stock_selected(None)
                break

    def show_loading(self):
        """Show loading indicator"""
        self.loading = True
        self.loading_frame.pack(fill=tk.X, pady=5)
        self.root.update_idletasks()

    def hide_loading(self):
        """Hide loading indicator"""
        self.loading = False
        self.loading_frame.pack_forget()
        self.root.update_idletasks()

    def on_stock_selected(self, event):
        """Handle stock selection"""
        if self.loading:
            return

        selected = self.stock_combo.get()
        if not selected:
            return

        # Show loading indicator
        self.show_loading()

        # Use a separate thread to load data
        threading.Thread(target=self.load_stock_data, args=(selected,), daemon=True).start()

    def load_stock_data(self, selected):
        """Load stock data in a background thread"""
        try:
            time.sleep(0.1)  # Small delay to ensure loading indicator appears

            # Parse company name and ticker
            company, ticker = selected.split(" | ")

            # Generate data
            self.current_stock = ticker
            self.stock_data = generate_stock_data(ticker)

            # Update UI in main thread
            self.root.after(0, lambda: self.update_ui(company, ticker))
        except Exception as e:
            print(f"Error loading stock data: {e}")
            traceback.print_exc()
            self.root.after(0, self.hide_loading)

    def update_ui(self, company, ticker):
        """Update UI with loaded stock data (called in main thread)"""
        try:
            # Basic stock info
            self.update_stock_info(company, ticker)

            # Update current view
            if self.current_view == "overview":
                self.update_price_chart()
            elif self.current_view == "historical":
                self.update_historical_data()
            elif self.current_view == "recommendation":
                self.update_recommendation()
        finally:
            # Hide loading indicator
            self.hide_loading()

    def update_stock_info(self, company, ticker):
        """Update stock information panel"""
        if self.stock_data is None or len(self.stock_data) < 2:
            return

        # Get latest data
        latest = self.stock_data.iloc[-1]
        prev = self.stock_data.iloc[-2]

        # Calculate price change
        price_change = latest['Close'] - prev['Close']
        price_change_pct = (price_change / prev['Close']) * 100

        # Company and ticker combined
        self.stock_info["company"].config(text=f"{company} ({ticker})")

        # Current price with larger font
        self.stock_info["price"].config(text=f"${latest['Close']:.2f}")

        # Price change with colors and background highlights
        change_text = f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        if price_change >= 0:
            self.stock_info["change"].config(text=change_text, foreground="green", background="#DFF0D8")
        else:
            self.stock_info["change"].config(text=change_text, foreground="red", background="#F2DEDE")

        # Update additional info
        self.stock_info["open"].config(text=f"${latest['Open']:.2f}")
        self.stock_info["dayhigh"].config(text=f"${latest['High']:.2f}")
        self.stock_info["daylow"].config(text=f"${latest['Low']:.2f}")
        self.stock_info["volume"].config(text=f"{latest['Volume']:,}")

    def update_price_chart(self):
        """Update price chart with stock data"""
        if self.stock_data is None or len(self.stock_data) < 1:
            return

        # Clear previous chart
        self.ax.clear()

        # Get the last 90 days of data (or less if not available)
        days = min(90, len(self.stock_data))
        data = self.stock_data.iloc[-days:]

        # Plot price data
        self.ax.plot(data.index, data['Close'], color=COLORS["accent"], linewidth=2, label='Price')

        # Add selected indicators
        self.add_indicators_to_chart(data)

        # Format the chart
        self.ax.set_title(f"{self.current_stock} - Price Chart", color=COLORS["header"])
        self.ax.set_xlabel('Date', color=COLORS["text"])
        self.ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["border"])

        # Format x-axis labels
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)

        # Add legend
        if any(indicator["var"].get() for indicator in self.indicators.values()):
            self.ax.legend(loc='upper left')

        # Update canvas
        self.canvas.draw()

    def add_indicators_to_chart(self, data):
        """Add selected technical indicators to the chart"""
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
                    # Calculate Bollinger Bands
                    sma = calculate_sma(data, period=20)
                    std = data['Close'].rolling(window=20).std()
                    upper_band = sma + (std * 2)
                    lower_band = sma - (std * 2)

                    # Plot bands
                    self.ax.plot(data.index, upper_band, color='green', linestyle='-', linewidth=1, alpha=0.5,
                                 label='Upper BB')
                    self.ax.plot(data.index, sma, color='orange', linestyle='-', linewidth=1, alpha=0.5,
                                 label='Middle BB')
                    self.ax.plot(data.index, lower_band, color='red', linestyle='-', linewidth=1, alpha=0.5,
                                 label='Lower BB')
                    self.ax.fill_between(data.index, upper_band, lower_band, alpha=0.1, color='gray')
                except Exception as e:
                    print(f"Error calculating Bollinger Bands: {e}")

            elif key == "rsi":
                try:
                    # Only calculate RSI if we have enough data
                    if len(data) > 14:
                        rsi = calculate_rsi(data)

                        # Create a second y-axis for RSI
                        ax2 = self.ax.twinx()
                        ax2.set_ylabel('RSI', color='orange')
                        ax2.plot(data.index, rsi, color='orange', linewidth=1.5, label='RSI (14)')
                        ax2.set_ylim([0, 100])

                        # Add overbought/oversold lines
                        ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5)
                        ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5)
                except Exception as e:
                    print(f"Error calculating RSI: {e}")

    def update_indicators(self):
        """Update chart when indicators are toggled"""
        if self.current_stock:
            self.update_price_chart()

    def update_historical_data(self):
        """Update historical data view"""
        if self.stock_data is None or len(self.stock_data) < 1:
            return

        # Update historical chart
        self.update_candlestick_chart()

        # Update historical data table
        self.update_historical_table()

    def update_candlestick_chart(self):
        """Update candlestick chart with stock data"""
        # Clear previous chart
        self.hist_ax.clear()

        # Get the last 30 days of data (or less if not available)
        days = min(30, len(self.stock_data))
        data = self.stock_data.iloc[-days:]

        # Plot candlestick chart
        for i in range(len(data)):
            date = data.index[i]
            open_price = data['Open'].iloc[i]
            close_price = data['Close'].iloc[i]
            high_price = data['High'].iloc[i]
            low_price = data['Low'].iloc[i]

            # Determine color based on price movement
            color = COLORS["positive"] if close_price >= open_price else COLORS["negative"]

            # Draw candlestick
            self.hist_ax.plot([date, date], [low_price, high_price], color=color, linewidth=1)
            self.hist_ax.bar(date, close_price - open_price, bottom=open_price, color=color, width=0.8, alpha=0.6)

        # Format the chart
        self.hist_ax.set_title(f"{self.current_stock} - Candlestick Chart", color=COLORS["header"])
        self.hist_ax.set_xlabel('Date', color=COLORS["text"])
        self.hist_ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.hist_ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["border"])

        # Format x-axis labels
        self.hist_ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        self.hist_ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(self.hist_ax.xaxis.get_majorticklabels(), rotation=45)

        # Update canvas
        self.hist_canvas.draw()

    def update_historical_table(self):
        """Update historical data table"""
        # Clear existing data
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        # Get number of rows to display (max 100 to avoid performance issues)
        num_rows = min(100, len(self.stock_data))

        # Insert data (newest first)
        for i in range(num_rows):
            idx = len(self.stock_data) - 1 - i
            row = self.stock_data.iloc[idx]
            date_str = row.name.strftime('%Y-%m-%d')

            # Format values
            open_price = f"${row['Open']:.2f}"
            high_price = f"${row['High']:.2f}"
            low_price = f"${row['Low']:.2f}"
            close_price = f"${row['Close']:.2f}"
            volume = f"{row['Volume']:,}"

            # Insert into treeview
            self.hist_tree.insert("", tk.END, values=(date_str, open_price, high_price, low_price, close_price, volume))

    def update_recommendation(self):
        """Update investment recommendation"""
        if self.stock_data is None or len(self.stock_data) < 20:
            return

        try:
            # Get current price and calculate basic metrics
            current_price = self.stock_data['Close'].iloc[-1]

            # Calculate 30-day and 90-day performance
            days_30_ago = min(30, len(self.stock_data) - 1)
            days_90_ago = min(90, len(self.stock_data) - 1)

            price_30d_ago = self.stock_data['Close'].iloc[-days_30_ago - 1]
            price_90d_ago = self.stock_data['Close'].iloc[-days_90_ago - 1]

            perf_30d = ((current_price / price_30d_ago) - 1) * 100
            perf_90d = ((current_price / price_90d_ago) - 1) * 100

            # Calculate technical indicators for analysis
            sma_20 = calculate_sma(self.stock_data, 20).iloc[-1]

            # Only calculate SMA-50 if we have enough data
            if len(self.stock_data) >= 50:
                sma_50 = calculate_sma(self.stock_data, 50).iloc[-1]
            else:
                sma_50 = None

            # Calculate RSI
            rsi = calculate_rsi(self.stock_data).iloc[-1]

            # Generate recommendation
            if current_price > sma_20 and (sma_50 is None or current_price > sma_50) and rsi < 70:
                recommendation = "BUY"
                rec_tag = "positive"
                reasoning = [
                    "Stock is trading above moving averages, indicating a positive trend.",
                    f"RSI of {rsi:.1f} suggests the stock is not yet overbought.",
                    f"The stock has shown a {perf_30d:.1f}% return over the last 30 days."
                ]
            elif current_price < sma_20 and (sma_50 is None or current_price < sma_50) and rsi > 30:
                recommendation = "SELL"
                rec_tag = "negative"
                reasoning = [
                    "Stock is trading below moving averages, indicating a negative trend.",
                    f"RSI of {rsi:.1f} suggests the stock is not yet oversold.",
                    f"The stock has shown a {perf_30d:.1f}% return over the last 30 days."
                ]
            elif rsi < 30:
                recommendation = "BUY (Oversold)"
                rec_tag = "positive"
                reasoning = [
                    "The RSI suggests oversold conditions.",
                    "This could represent a potential value opportunity.",
                    "However, caution is advised as the trend may continue."
                ]
            elif rsi > 70:
                recommendation = "SELL (Overbought)"
                rec_tag = "negative"
                reasoning = [
                    "The RSI suggests overbought conditions.",
                    "Consider taking profits if currently holding this position.",
                    "However, strong momentum might continue in the short term."
                ]
            else:
                recommendation = "HOLD"
                rec_tag = "neutral"
                reasoning = [
                    "The stock is showing mixed signals based on technical indicators.",
                    f"The RSI of {rsi:.1f} is in neutral territory.",
                    "Consider your investment goals and risk tolerance."
                ]

            # Calculate volatility (simplified)
            returns = self.stock_data['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility

            # Update the recommendation text widget
            self.rec_text.config(state=tk.NORMAL)
            self.rec_text.delete(1.0, tk.END)

            # Title
            self.rec_text.insert(tk.END, f"Investment Recommendation for {self.current_stock}\n\n", "title")

            # Summary
            self.rec_text.insert(tk.END, "Summary\n", "header")
            self.rec_text.insert(tk.END, "Current Recommendation: ")
            self.rec_text.insert(tk.END, f"{recommendation}\n\n", rec_tag)

            self.rec_text.insert(tk.END, f"Current Price: ${current_price:.2f}\n")

            # Performance
            self.rec_text.insert(tk.END, "30-Day Performance: ")
            if perf_30d >= 0:
                self.rec_text.insert(tk.END, f"{perf_30d:.2f}%\n", "positive")
            else:
                self.rec_text.insert(tk.END, f"{perf_30d:.2f}%\n", "negative")

            self.rec_text.insert(tk.END, "90-Day Performance: ")
            if perf_90d >= 0:
                self.rec_text.insert(tk.END, f"{perf_90d:.2f}%\n\n", "positive")
            else:
                self.rec_text.insert(tk.END, f"{perf_90d:.2f}%\n\n", "negative")

            # Technical Analysis
            self.rec_text.insert(tk.END, "Technical Analysis\n", "header")

            # Moving Averages
            self.rec_text.insert(tk.END, "• 20-Day SMA: ")
            if current_price > sma_20:
                self.rec_text.insert(tk.END, f"${sma_20:.2f} (Price Above)\n", "positive")
            else:
                self.rec_text.insert(tk.END, f"${sma_20:.2f} (Price Below)\n", "negative")

            if sma_50 is not None:
                self.rec_text.insert(tk.END, "• 50-Day SMA: ")
                if current_price > sma_50:
                    self.rec_text.insert(tk.END, f"${sma_50:.2f} (Price Above)\n", "positive")
                else:
                    self.rec_text.insert(tk.END, f"${sma_50:.2f} (Price Below)\n", "negative")

            # RSI
            self.rec_text.insert(tk.END, "• RSI (14): ")
            if rsi > 70:
                self.rec_text.insert(tk.END, f"{rsi:.2f} (Overbought)\n", "negative")
            elif rsi < 30:
                self.rec_text.insert(tk.END, f"{rsi:.2f} (Oversold)\n", "positive")
            else:
                self.rec_text.insert(tk.END, f"{rsi:.2f} (Neutral)\n", "neutral")

            # Volatility
            self.rec_text.insert(tk.END, "• Volatility (Annualized): ")
            if volatility > 30:
                self.rec_text.insert(tk.END, f"{volatility:.2f}% (High)\n\n", "negative")
            elif volatility > 15:
                self.rec_text.insert(tk.END, f"{volatility:.2f}% (Moderate)\n\n", "neutral")
            else:
                self.rec_text.insert(tk.END, f"{volatility:.2f}% (Low)\n\n", "positive")

            # Reasoning
            self.rec_text.insert(tk.END, "Reasoning\n", "header")
            for reason in reasoning:
                self.rec_text.insert(tk.END, f"• {reason}\n")

            # Disclaimer
            self.rec_text.insert(tk.END,
                                 "\nDisclaimer: This recommendation is based solely on technical analysis and does not take into account fundamental factors. This is not financial advice.")

            self.rec_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error updating recommendation: {e}")
            traceback.print_exc()

            # Show error message
            self.rec_text.config(state=tk.NORMAL)
            self.rec_text.delete(1.0, tk.END)
            self.rec_text.insert(tk.END, "Error generating recommendation. Please try again.")
            self.rec_text.config(state=tk.DISABLED)

    def show_section(self, section):
        """Switch between different views"""
        # Update current view
        self.current_view = section

        # Update active button style
        for key, button in self.nav_buttons.items():
            if key == section:
                button.configure(style="Active.Nav.TButton")
            else:
                button.configure(style="Nav.TButton")

        # Hide all frames
        for frame in self.content_frames.values():
            frame.pack_forget()

        # Show selected frame
        self.content_frames[section].pack(fill=tk.BOTH, expand=True)

        # Update content if we have a stock selected
        if self.current_stock:
            if section == "overview":
                self.update_price_chart()
            elif section == "historical":
                self.update_historical_data()
            elif section == "recommendation":
                self.update_recommendation()


def main():
    root = tk.Tk()

    # Set icon and title
    root.title("Financial Data Analytics Software")

    try:
        # Create application
        app = FinancialAnalyticsApp(root)

        # Start mainloop
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()

        # Show error message dialog
        tk.messagebox.showerror("Error", f"An error occurred starting the application:\n\n{str(e)}")


if __name__ == "__main__":
    main()