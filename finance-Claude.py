import tkinter as tk
from tkinter import ttk, messagebox, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
import matplotlib.dates as mdates

# Define color scheme for financial app - Professional finance theme
# Using a lighter color scheme with appropriate accent colors
COLORS = {
    "bg_dark": "#34495E",  # Light gray background
    "bg_medium": "#FFFFFF",  # White for panels
    "bg_light": "#FFFFFF",  # White for inputs
    "text": "#333333",  # Dark gray text
    "accent": "#1E88E5",  # Blue accent for buttons and highlights
    "positive": "#26A69A",  # Teal green for positive values
    "negative": "#EF5350",  # Light red for negative values
    "neutral": "#FFA726",  # Orange for neutral/warning
    "header": "#212121",  # Very dark gray for headers
    "border": "#E0E0E0",  # Light gray for borders
    "highlight": "#E3F2FD",  # Very light blue for highlights
    "chart_bg": "#FAFAFA",  # Almost white for chart background
    "grid": "#EEEEEE",  # Very light gray for grid lines
}


# Generate simulated stock data
def generate_stock_data(ticker, days=365):
    np.random.seed(hash(ticker) % 100)  # Different seed for each ticker but consistent

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start_date, end_date)

    # Starting price between 50 and 500
    start_price = np.random.randint(50, 500)

    # Generate daily price movements with some randomness and trend
    price_changes = np.random.normal(0, 0.015, len(date_range))

    # Add a slight trend based on ticker
    trend = (hash(ticker) % 7 - 3) / 100  # Between -0.03 and 0.03
    price_changes += trend

    # Calculate prices
    prices = start_price * (1 + price_changes).cumprod()

    # Generate OHLC data
    data = pd.DataFrame(index=date_range)
    data['Date'] = date_range
    data['Close'] = prices

    # Create Open, High, Low with reasonable variation from Close
    daily_volatility = prices * np.random.uniform(0.005, 0.02, len(prices))
    data['Open'] = prices * (1 + np.random.uniform(-0.01, 0.01, len(prices)))
    data['High'] = np.maximum(data['Open'], data['Close']) + daily_volatility
    data['Low'] = np.minimum(data['Open'], data['Close']) - daily_volatility

    # Ensure High >= Open, Close and Low <= Open, Close
    data['High'] = np.maximum(data['High'], np.maximum(data['Open'], data['Close']))
    data['Low'] = np.minimum(data['Low'], np.minimum(data['Open'], data['Close']))

    # Generate volume (in thousands)
    data['Volume'] = np.random.randint(100, 10000, len(date_range))

    # Add some anomalies and events
    # - Simulate a few high volatility days
    high_vol_days = np.random.choice(len(date_range), size=5, replace=False)
    data.loc[data.index[high_vol_days], 'High'] *= np.random.uniform(1.05, 1.15, 5)
    data.loc[data.index[high_vol_days], 'Low'] *= np.random.uniform(0.85, 0.95, 5)
    data.loc[data.index[high_vol_days], 'Volume'] *= np.random.uniform(2, 4, 5)

    return data


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
    ("Visa Inc.", "V"),
    ("Johnson & Johnson", "JNJ"),
    ("Walmart Inc.", "WMT"),
    ("Procter & Gamble Co.", "PG"),
    ("Mastercard Inc.", "MA"),
    ("UnitedHealth Group Inc.", "UNH"),
    ("Exxon Mobil Corporation", "XOM"),
    ("Chevron Corporation", "CVX"),
    ("Home Depot Inc.", "HD"),
    ("Coca-Cola Company", "KO"),
    ("PepsiCo Inc.", "PEP")
]


# Technical Indicators Implementation
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


def calculate_bollinger_bands(data, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = calculate_sma(data, period)
    std = data['Close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    fast_ema = data['Close'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = data['Close'].ewm(span=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_atr(data, period=14):
    """Calculate Average True Range"""
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean()
    return atr


class FinancialAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Data Analytics Software")
        self.root.geometry("1280x800")
        self.root.configure(bg=COLORS["bg_dark"])

        # Create custom fonts
        self.title_font = font.Font(family="Arial", size=14, weight="bold")
        self.header_font = font.Font(family="Arial", size=12, weight="bold")
        self.normal_font = font.Font(family="Arial", size=10)
        self.small_font = font.Font(family="Arial", size=9)
        self.mono_font = font.Font(family="Courier New", size=10)

        # Set default font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Arial", size=10)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(family="Arial", size=10)

        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configure frame styles
        self.style.configure("TFrame", background=COLORS["bg_medium"])
        self.style.configure("App.TFrame", background=COLORS["bg_dark"])
        self.style.configure("Card.TFrame", background=COLORS["bg_medium"], relief="raised")

        # Configure label styles
        self.style.configure("TLabel", background=COLORS["bg_medium"], foreground=COLORS["text"])
        self.style.configure("App.TLabel", background=COLORS["bg_dark"], foreground=COLORS["text"])
        self.style.configure("Title.TLabel", background=COLORS["bg_medium"], foreground=COLORS["header"],
                             font=self.title_font)
        self.style.configure("Header.TLabel", background=COLORS["bg_medium"], foreground=COLORS["header"],
                             font=self.header_font)
        self.style.configure("Bold.TLabel", background=COLORS["bg_medium"], foreground=COLORS["text"],
                             font=self.header_font)
        self.style.configure("Value.TLabel", background=COLORS["bg_medium"], foreground=COLORS["text"],
                             font=self.normal_font)
        self.style.configure("Positive.TLabel", background=COLORS["bg_medium"], foreground=COLORS["positive"],
                             font=self.normal_font)
        self.style.configure("Negative.TLabel", background=COLORS["bg_medium"], foreground=COLORS["negative"],
                             font=self.normal_font)

        # Configure button styles
        self.style.configure("TButton", background=COLORS["accent"], foreground="white", borderwidth=0,
                             focusthickness=0, font=self.normal_font)
        self.style.map("TButton",
                       background=[('active', COLORS["accent"]), ('pressed', '#1565C0')],
                       relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        self.style.configure("Nav.TButton", background=COLORS["bg_medium"], foreground=COLORS["text"],
                             font=self.normal_font)
        self.style.map("Nav.TButton",
                       background=[('active', COLORS["highlight"]), ('pressed', COLORS["highlight"])],
                       foreground=[('active', COLORS["accent"]), ('pressed', COLORS["accent"])])
        self.style.configure("Active.Nav.TButton", background=COLORS["highlight"], foreground=COLORS["accent"],
                             font=self.normal_font)

        # Configure checkbutton style
        self.style.configure("TCheckbutton", background=COLORS["bg_medium"], foreground=COLORS["text"],
                             font=self.normal_font)
        self.style.map("TCheckbutton",
                       background=[('active', COLORS["bg_medium"])],
                       foreground=[('active', COLORS["accent"])])

        # Configure combobox style
        self.style.configure("TCombobox", selectbackground=COLORS["accent"], selectforeground="white")
        self.style.map("TCombobox",
                       fieldbackground=[('readonly', COLORS["bg_medium"])],
                       selectbackground=[('readonly', COLORS["accent"])])

        # Configure separator style
        self.style.configure("TSeparator", background=COLORS["border"])

        # Configure treeview style
        self.style.configure("Treeview",
                             background=COLORS["bg_medium"],
                             foreground=COLORS["text"],
                             fieldbackground=COLORS["bg_medium"],
                             font=self.normal_font)
        self.style.configure("Treeview.Heading",
                             background=COLORS["accent"],
                             foreground="white",
                             font=self.normal_font,
                             relief="flat")
        self.style.map("Treeview.Heading",
                       background=[('active', COLORS["accent"])])

        # Stock data
        self.current_stock = None
        self.stock_data = None
        self.current_view = "overview"

        # Create UI components
        self.create_ui()

    def create_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, style="App.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header frame
        header_frame = ttk.Frame(main_frame, style="App.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # App title
        ttk.Label(header_frame, text="Financial Data Analytics", style="Title.TLabel", font=self.title_font).pack(
            side=tk.LEFT)

        # Content frame (contains left and right panels)
        content_frame = ttk.Frame(main_frame, style="App.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel (controls)
        left_frame = ttk.Frame(content_frame, style="App.TFrame", width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)  # Prevent shrinking

        # Stock selection card
        stock_card = ttk.Frame(left_frame, style="Card.TFrame")
        stock_card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(stock_card, text="Stock Selection", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 15))
        ttk.Separator(stock_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Stock selection content
        stock_content = ttk.Frame(stock_card, style="TFrame")
        stock_content.pack(fill=tk.X, padx=15)

        ttk.Label(stock_content, text="Select Stock:", style="TLabel").pack(anchor=tk.W, pady=(0, 5))

        # Combobox for stock selection
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(stock_content, textvariable=self.stock_var, state="readonly", width=30,
                                        font=self.normal_font)
        stock_options = [f"{name} | {ticker}" for name, ticker in STOCKS]
        self.stock_combo['values'] = stock_options
        self.stock_combo.pack(fill=tk.X)
        self.stock_combo.bind("<<ComboboxSelected>>", self.on_stock_selected)

        # Technical indicators card
        indicators_card = ttk.Frame(left_frame, style="Card.TFrame")
        indicators_card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(indicators_card, text="Technical Indicators", style="Header.TLabel").pack(anchor=tk.W, padx=15,
                                                                                            pady=(10, 15))
        ttk.Separator(indicators_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Indicators content
        indicators_content = ttk.Frame(indicators_card, style="TFrame")
        indicators_content.pack(fill=tk.X, padx=15)

        # Checkboxes for technical indicators
        self.indicators = {
            "sma": {"var": tk.BooleanVar(), "name": "Simple Moving Average (SMA)", "compatible": True},
            "ema": {"var": tk.BooleanVar(), "name": "Exponential Moving Average (EMA)", "compatible": True},
            "bollinger": {"var": tk.BooleanVar(), "name": "Bollinger Bands", "compatible": True},
            "rsi": {"var": tk.BooleanVar(), "name": "Relative Strength Index (RSI)", "compatible": False},
            "macd": {"var": tk.BooleanVar(), "name": "MACD", "compatible": False},
            "atr": {"var": tk.BooleanVar(), "name": "Average True Range (ATR)", "compatible": False}
        }

        for key, indicator in self.indicators.items():
            cb = ttk.Checkbutton(
                indicators_content,
                text=indicator["name"],
                variable=indicator["var"],
                command=self.update_indicators,
                style="TCheckbutton"
            )
            cb.pack(anchor=tk.W, pady=3)

        # Navigation card
        nav_card = ttk.Frame(left_frame, style="Card.TFrame")
        nav_card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(nav_card, text="Navigation", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 15))
        ttk.Separator(nav_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Navigation content
        nav_content = ttk.Frame(nav_card, style="TFrame")
        nav_content.pack(fill=tk.X, padx=15)

        # Navigation buttons
        self.nav_buttons = {}
        nav_options = [
            ("overview", "Overview"),
            ("historical", "Historical Data"),
            ("recommendation", "Investment Recommendation")
        ]

        for key, text in nav_options:
            btn = ttk.Button(
                nav_content,
                text=text,
                command=lambda k=key: self.show_section(k),
                style="Nav.TButton"
            )
            btn.pack(fill=tk.X, pady=3, ipady=5)
            self.nav_buttons[key] = btn

        # Update active nav button style
        self.nav_buttons["overview"].configure(style="Active.Nav.TButton")

        # Right panel (display area)
        self.right_frame = ttk.Frame(content_frame, style="App.TFrame")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Content frames (stacked)
        self.content_frames = {}

        # Overview frame
        self.content_frames["overview"] = ttk.Frame(self.right_frame, style="App.TFrame")

        # Stock info card
        self.stock_info_card = ttk.Frame(self.content_frames["overview"], style="Card.TFrame")
        self.stock_info_card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(self.stock_info_card, text="Stock Information", style="Header.TLabel").pack(anchor=tk.W, padx=15,
                                                                                              pady=(10, 15))
        ttk.Separator(self.stock_info_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Stock info content
        stock_info_content = ttk.Frame(self.stock_info_card, style="TFrame")
        stock_info_content.pack(fill=tk.X, padx=15)

        # Stock info grid
        self.stock_info = {}
        info_items = [
            ("company", "Company:"),
            ("ticker", "Ticker:"),
            ("price", "Current Price:"),
            ("change", "Change:"),
            ("open", "Open:"),
            ("high", "Day High:"),
            ("low", "Day Low:"),
            ("volume", "Volume:"),
        ]

        # Create a 2x4 grid for stock info
        for i, (key, label) in enumerate(info_items):
            row, col = i // 4, i % 4
            ttk.Label(stock_info_content, text=label, style="Bold.TLabel").grid(row=row, column=col * 2, sticky=tk.W,
                                                                                padx=(20 if col else 0, 5), pady=5)
            self.stock_info[key] = ttk.Label(stock_info_content, text="--", style="Value.TLabel")
            self.stock_info[key].grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=(0, 20), pady=5)

        # Chart card
        chart_card = ttk.Frame(self.content_frames["overview"], style="Card.TFrame")
        chart_card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        # Card title
        ttk.Label(chart_card, text="Price Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15, pady=(10, 15))
        ttk.Separator(chart_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Chart content
        chart_content = ttk.Frame(chart_card, style="TFrame")
        chart_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Create matplotlib figure for chart
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor(COLORS["chart_bg"])
        self.ax.set_facecolor(COLORS["chart_bg"])

        # Add color to the ticks
        self.ax.tick_params(axis='x', colors=COLORS["text"])
        self.ax.tick_params(axis='y', colors=COLORS["text"])

        # Change the color of the axes
        for spine in self.ax.spines.values():
            spine.set_edgecolor(COLORS["text"])

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_content)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Historical data frame
        self.content_frames["historical"] = ttk.Frame(self.right_frame, style="App.TFrame")

        # Historical chart card
        hist_chart_card = ttk.Frame(self.content_frames["historical"], style="Card.TFrame")
        hist_chart_card.pack(fill=tk.X, pady=(0, 10), padx=5, ipady=10)

        # Card title
        ttk.Label(hist_chart_card, text="Candlestick Chart", style="Header.TLabel").pack(anchor=tk.W, padx=15,
                                                                                         pady=(10, 15))
        ttk.Separator(hist_chart_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Chart content
        hist_chart_content = ttk.Frame(hist_chart_card, style="TFrame")
        hist_chart_content.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Create matplotlib figure for historical chart (candlestick)
        self.hist_fig, self.hist_ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.hist_fig.patch.set_facecolor(COLORS["chart_bg"])
        self.hist_ax.set_facecolor(COLORS["chart_bg"])

        # Add color to the ticks
        self.hist_ax.tick_params(axis='x', colors=COLORS["text"])
        self.hist_ax.tick_params(axis='y', colors=COLORS["text"])

        # Change the color of the axes
        for spine in self.hist_ax.spines.values():
            spine.set_edgecolor(COLORS["text"])

        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=hist_chart_content)
        # Configure the chart height
        self.hist_canvas.get_tk_widget().configure(height=300)
        self.hist_canvas.get_tk_widget().pack(fill=tk.X)

        # Historical data table card
        hist_table_card = ttk.Frame(self.content_frames["historical"], style="Card.TFrame")
        hist_table_card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        # Card title
        ttk.Label(hist_table_card, text="Historical Data", style="Header.TLabel").pack(anchor=tk.W, padx=15,
                                                                                       pady=(10, 15))
        ttk.Separator(hist_table_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Table content
        hist_table_content = ttk.Frame(hist_table_card, style="TFrame")
        hist_table_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Create treeview for historical data
        columns = ("Date", "Open", "High", "Low", "Close", "Volume")
        self.hist_tree = ttk.Treeview(hist_table_content, columns=columns, show="headings", height=15)

        # Set column headings
        for col in columns:
            self.hist_tree.heading(col, text=col)
            self.hist_tree.column(col, width=100, anchor=tk.CENTER)

        # Add scrollbar to treeview
        tree_scroll = ttk.Scrollbar(hist_table_content, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=tree_scroll.set)

        # Pack treeview and scrollbar
        self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Investment recommendation frame
        self.content_frames["recommendation"] = ttk.Frame(self.right_frame, style="App.TFrame")

        # Recommendation card
        rec_card = ttk.Frame(self.content_frames["recommendation"], style="Card.TFrame")
        rec_card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=10)

        # Card title
        ttk.Label(rec_card, text="Investment Recommendation", style="Header.TLabel").pack(anchor=tk.W, padx=15,
                                                                                          pady=(10, 15))
        ttk.Separator(rec_card, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=(0, 15))

        # Recommendation content
        rec_content = ttk.Frame(rec_card, style="TFrame")
        rec_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Create text widget for recommendation
        self.rec_text = tk.Text(rec_content, wrap=tk.WORD,
                                bg=COLORS["bg_medium"], fg=COLORS["text"],
                                bd=0, highlightthickness=0, padx=5, pady=5,
                                font=self.normal_font)
        rec_scroll = ttk.Scrollbar(rec_content, orient="vertical", command=self.rec_text.yview)
        self.rec_text.configure(yscrollcommand=rec_scroll.set)

        self.rec_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rec_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.rec_text.config(state=tk.DISABLED)  # Make it read-only

        # Configure tags for styling text
        self.rec_text.tag_configure("title", font=self.title_font, foreground=COLORS["header"])
        self.rec_text.tag_configure("header", font=self.header_font, foreground=COLORS["header"])
        self.rec_text.tag_configure("bold", font=font.Font(family="Arial", size=10, weight="bold"))
        self.rec_text.tag_configure("positive", foreground=COLORS["positive"])
        self.rec_text.tag_configure("negative", foreground=COLORS["negative"])
        self.rec_text.tag_configure("neutral", foreground=COLORS["neutral"])

        # Show default section
        self.show_section("overview")

        # Set placeholder message
        self.show_placeholder()

    def show_placeholder(self):
        """Show placeholder message when no stock is selected"""
        # Clear the chart
        self.ax.clear()
        self.ax.text(0.5, 0.5, "Select a stock to view data",
                     horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes, fontsize=14, color=COLORS["text"])
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()

        # Clear the historical chart
        self.hist_ax.clear()
        self.hist_ax.text(0.5, 0.5, "Select a stock to view historical data",
                          horizontalalignment='center', verticalalignment='center',
                          transform=self.hist_ax.transAxes, fontsize=14, color=COLORS["text"])
        self.hist_ax.set_xticks([])
        self.hist_ax.set_yticks([])
        self.hist_canvas.draw()

        # Clear the table
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        # Clear recommendation text
        self.rec_text.config(state=tk.NORMAL)
        self.rec_text.delete(1.0, tk.END)
        self.rec_text.insert(tk.END, "Select a stock to view investment recommendations.")
        self.rec_text.config(state=tk.DISABLED)

    def on_stock_selected(self, event):
        selected = self.stock_combo.get()
        if selected:
            # Parse company name and ticker
            company, ticker = selected.split(" | ")

            # Generate data for this stock
            self.current_stock = ticker
            self.stock_data = generate_stock_data(ticker)

            # Update UI with stock data
            self.update_stock_info(company, ticker)
            self.update_price_chart()
            self.update_historical_data()
            self.update_recommendation()

            # Reset indicators
            for indicator in self.indicators.values():
                indicator["var"].set(False)

    def update_stock_info(self, company, ticker):
        """Update the stock information panel with latest data"""
        # Get the most recent data
        latest_data = self.stock_data.iloc[-1]
        prev_data = self.stock_data.iloc[-2]

        # Calculate price change
        price_change = latest_data['Close'] - prev_data['Close']
        price_change_pct = (price_change / prev_data['Close']) * 100

        # Format the change string with color
        change_str = f"{price_change:.2f} ({price_change_pct:.2f}%)"

        # Update stock info labels
        self.stock_info["company"].config(text=company)
        self.stock_info["ticker"].config(text=ticker)
        self.stock_info["price"].config(text=f"${latest_data['Close']:.2f}")

        # Set color for price change
        if price_change >= 0:
            self.stock_info["change"].config(text=change_str, style="Positive.TLabel")
        else:
            self.stock_info["change"].config(text=change_str, style="Negative.TLabel")

        self.stock_info["open"].config(text=f"${latest_data['Open']:.2f}")
        self.stock_info["high"].config(text=f"${latest_data['High']:.2f}")
        self.stock_info["low"].config(text=f"${latest_data['Low']:.2f}")
        self.stock_info["volume"].config(text=f"{latest_data['Volume']:,}")

    def update_price_chart(self):
        """Update the main price chart with selected indicators"""
        # If there's no stock data, show placeholder
        if self.stock_data is None:
            return

        # Clear previous chart
        self.ax.clear()

        # Get the last 90 days of data
        data = self.stock_data.iloc[-90:]

        # Plot price data
        self.ax.plot(data.index, data['Close'], color=COLORS["accent"], linewidth=2, label='Price')

        # Format the chart
        self.ax.set_title(f"{self.current_stock} - Price Last 90 Days", color=COLORS["header"])
        self.ax.set_xlabel('Date', color=COLORS["text"])
        self.ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["grid"])

        # Format x-axis date labels
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)

        # Update the canvas
        self.canvas.draw()

        # Call update_indicators to ensure any selected indicators are shown
        self.update_indicators()

    def update_indicators(self):
        """Update chart with selected technical indicators"""
        # Check what indicators are selected
        if self.stock_data is None:
            return

        # Get selected indicators
        selected_indicators = [key for key, indicator in self.indicators.items() if indicator["var"].get()]

        # If no indicators are selected, just update the basic price chart
        if not selected_indicators:
            self.update_price_chart()
            return

        # Clear previous chart
        self.ax.clear()

        # Get the last 90 days of data
        data = self.stock_data.iloc[-90:]

        # Always plot price data
        self.ax.plot(data.index, data['Close'], color=COLORS["accent"], linewidth=2, label='Price')

        # Create a second y-axis for indicators that use different scale
        ax2 = None

        # Add selected indicators
        for key, indicator in self.indicators.items():
            if indicator["var"].get():
                if key == "sma":
                    sma = calculate_sma(data, period=20)
                    self.ax.plot(data.index, sma, color='#4CAF50', linestyle='--', linewidth=1.5, label='SMA (20)')

                elif key == "ema":
                    ema = calculate_ema(data, period=20)
                    self.ax.plot(data.index, ema, color='#F44336', linestyle='--', linewidth=1.5, label='EMA (20)')

                elif key == "bollinger":
                    upper, middle, lower = calculate_bollinger_bands(data)
                    self.ax.plot(data.index, upper, color='#4CAF50', linestyle='-', linewidth=1, alpha=0.5,
                                 label='Upper BB')
                    self.ax.plot(data.index, middle, color='#FFC107', linestyle='-', linewidth=1, alpha=0.5,
                                 label='Middle BB')
                    self.ax.plot(data.index, lower, color='#F44336', linestyle='-', linewidth=1, alpha=0.5,
                                 label='Lower BB')
                    self.ax.fill_between(data.index, upper, lower, alpha=0.1, color='#E0E0E0')

                elif key == "rsi":
                    # Create second y-axis if not already created
                    if ax2 is None:
                        ax2 = self.ax.twinx()
                        ax2.set_ylabel('RSI', color=COLORS["text"])
                        ax2.tick_params(axis='y', colors=COLORS["text"])

                    rsi = calculate_rsi(data)
                    ax2.plot(data.index, rsi, color='#FF9800', linestyle='-', linewidth=1.5, label='RSI (14)')

                    # Add overbought/oversold lines
                    ax2.axhline(y=70, color='#F44336', linestyle='--', alpha=0.5)
                    ax2.axhline(y=30, color='#4CAF50', linestyle='--', alpha=0.5)

                    # Set y-axis limits for RSI
                    ax2.set_ylim([0, 100])

                elif key == "macd":
                    if ax2 is None:
                        ax2 = self.ax.twinx()
                        ax2.set_ylabel('MACD', color=COLORS["text"])
                        ax2.tick_params(axis='y', colors=COLORS["text"])

                    macd_line, signal_line, histogram = calculate_macd(data)

                    # Plot MACD components
                    ax2.plot(data.index, macd_line, color='#2196F3', linestyle='-', linewidth=1.5, label='MACD Line')
                    ax2.plot(data.index, signal_line, color='#9C27B0', linestyle='--', linewidth=1.5,
                             label='Signal Line')

                    # Plot histogram as bar chart
                    for i, (date, value) in enumerate(zip(data.index, histogram)):
                        color = COLORS["positive"] if value >= 0 else COLORS["negative"]
                        ax2.bar(date, value, width=1, color=color, alpha=0.5)

                elif key == "atr":
                    if ax2 is None:
                        ax2 = self.ax.twinx()
                        ax2.set_ylabel('ATR', color=COLORS["text"])
                        ax2.tick_params(axis='y', colors=COLORS["text"])

                    atr = calculate_atr(data)
                    ax2.plot(data.index, atr, color='#00BCD4', linestyle='-', linewidth=1.5, label='ATR (14)')

        # Format the chart
        self.ax.set_title(f"{self.current_stock} - Price & Indicators", color=COLORS["header"])
        self.ax.set_xlabel('Date', color=COLORS["text"])
        self.ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["grid"])

        # Format x-axis date labels
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)

        # Add legend with appropriate handles
        handles1, labels1 = self.ax.get_legend_handles_labels()
        if ax2 is not None:
            handles2, labels2 = ax2.get_legend_handles_labels()
            self.ax.legend(handles1 + handles2, labels1 + labels2, loc='upper left')
        else:
            self.ax.legend(loc='upper left')

        # Update the canvas
        self.canvas.draw()

    def update_historical_data(self):
        """Update the historical data view with candlestick chart and data table"""
        if self.stock_data is None:
            return

        # Update historical chart (candlestick)
        self.hist_ax.clear()

        # Get the last 30 days of data for the candlestick chart
        data = self.stock_data.iloc[-30:]

        # Plot candlestick chart
        for i in range(len(data)):
            date = data.index[i]
            open_price = data['Open'].iloc[i]
            close_price = data['Close'].iloc[i]
            high_price = data['High'].iloc[i]
            low_price = data['Low'].iloc[i]

            # Determine color based on price movement
            color = COLORS["positive"] if close_price >= open_price else COLORS["negative"]

            # Draw the candlestick
            self.hist_ax.plot([date, date], [low_price, high_price], color=color, linewidth=1)
            self.hist_ax.bar(date, close_price - open_price, bottom=open_price, color=color, width=0.8, alpha=0.6)

        # Format the chart
        self.hist_ax.set_title(f"{self.current_stock} - Candlestick Chart (Last 30 Days)", color=COLORS["header"])
        self.hist_ax.set_xlabel('Date', color=COLORS["text"])
        self.hist_ax.set_ylabel('Price ($)', color=COLORS["text"])
        self.hist_ax.grid(True, linestyle='--', alpha=0.7, color=COLORS["grid"])

        # Format x-axis date labels
        self.hist_ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.hist_ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.setp(self.hist_ax.xaxis.get_majorticklabels(), rotation=45)

        # Update the canvas
        self.hist_canvas.draw()

        # Update historical data table
        # Clear existing data
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        # Insert new data (in reverse order - newest first)
        for i in range(len(self.stock_data) - 1, -1, -1):
            row = self.stock_data.iloc[i]
            date_str = row.name.strftime('%Y-%m-%d')

            # Format values
            open_price = f"${row['Open']:.2f}"
            high_price = f"${row['High']:.2f}"
            low_price = f"${row['Low']:.2f}"
            close_price = f"${row['Close']:.2f}"
            volume = f"{row['Volume']:,}"

            self.hist_tree.insert("", tk.END, values=(date_str, open_price, high_price, low_price, close_price, volume))

    def update_recommendation(self):
        """Update the investment recommendation based on technical analysis"""
        if self.stock_data is None:
            return

        # Calculate current price and basic metrics
        current_price = self.stock_data['Close'].iloc[-1]
        price_30d_ago = self.stock_data['Close'].iloc[-31] if len(self.stock_data) > 30 else \
        self.stock_data['Close'].iloc[0]
        price_90d_ago = self.stock_data['Close'].iloc[-91] if len(self.stock_data) > 90 else \
        self.stock_data['Close'].iloc[0]

        # Calculate technical indicators for analysis
        sma_20 = calculate_sma(self.stock_data, 20).iloc[-1]
        sma_50 = calculate_sma(self.stock_data, 50).iloc[-1]
        rsi = calculate_rsi(self.stock_data).iloc[-1]
        upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(self.stock_data)

        # Determine price performance
        perf_30d = ((current_price / price_30d_ago) - 1) * 100
        perf_90d = ((current_price / price_90d_ago) - 1) * 100

        # Generate recommendation based on technical indicators
        if current_price > sma_20 and current_price > sma_50 and rsi < 70:
            recommendation = "BUY"
            rec_tag = "positive"
            reasoning = [
                f"The stock is trading above both its 20-day and 50-day moving averages, indicating a positive trend.",
                f"The RSI of {rsi:.1f} suggests the stock is not yet in overbought territory.",
                f"The stock has shown a {perf_30d:.1f}% return over the last 30 days."
            ]
        elif current_price < sma_20 and current_price < sma_50 and rsi > 30:
            recommendation = "SELL"
            rec_tag = "negative"
            reasoning = [
                f"The stock is trading below both its 20-day and 50-day moving averages, indicating a negative trend.",
                f"The RSI of {rsi:.1f} suggests the stock is not yet in oversold territory.",
                f"The stock has shown a {perf_30d:.1f}% return over the last 30 days."
            ]
        elif current_price < lower_bb.iloc[-1] and rsi < 30:
            recommendation = "BUY (Oversold)"
            rec_tag = "positive"
            reasoning = [
                f"The stock is trading below the lower Bollinger Band, suggesting it may be oversold.",
                f"The RSI of {rsi:.1f} confirms oversold conditions.",
                f"This could represent a potential value opportunity, though caution is advised."
            ]
        elif current_price > upper_bb.iloc[-1] and rsi > 70:
            recommendation = "SELL (Overbought)"
            rec_tag = "negative"
            reasoning = [
                f"The stock is trading above the upper Bollinger Band, suggesting it may be overbought.",
                f"The RSI of {rsi:.1f} confirms overbought conditions.",
                f"Consider taking profits if you currently hold this position."
            ]
        else:
            recommendation = "HOLD"
            rec_tag = "neutral"
            reasoning = [
                f"The stock is showing mixed signals based on technical indicators.",
                f"The price is between the 20-day and 50-day moving averages.",
                f"The RSI of {rsi:.1f} is in neutral territory."
            ]

        # Generate additional insights
        volume_avg = self.stock_data['Volume'].rolling(window=20).mean().iloc[-1]
        latest_volume = self.stock_data['Volume'].iloc[-1]
        volume_ratio = latest_volume / volume_avg

        volatility = self.stock_data['Close'].pct_change().std() * np.sqrt(252) * 100  # Annualized volatility

        # Update the recommendation text widget with styled text
        self.rec_text.config(state=tk.NORMAL)
        self.rec_text.delete(1.0, tk.END)

        # Title
        self.rec_text.insert(tk.END, f"Investment Recommendation for {self.current_stock}\n\n", "title")

        # Summary section
        self.rec_text.insert(tk.END, "Summary\n", "header")
        self.rec_text.insert(tk.END, "Current Recommendation: ", "bold")
        self.rec_text.insert(tk.END, f"{recommendation}\n\n", rec_tag)

        self.rec_text.insert(tk.END, f"Current Price: ${current_price:.2f}\n", "bold")

        # Format 30-day performance with color
        self.rec_text.insert(tk.END, "30-Day Performance: ", "bold")
        tag = "positive" if perf_30d >= 0 else "negative"
        self.rec_text.insert(tk.END, f"{perf_30d:.2f}%\n", tag)

        # Format 90-day performance with color
        self.rec_text.insert(tk.END, "90-Day Performance: ", "bold")
        tag = "positive" if perf_90d >= 0 else "negative"
        self.rec_text.insert(tk.END, f"{perf_90d:.2f}%\n\n", tag)

        # Technical Analysis section
        self.rec_text.insert(tk.END, "Technical Analysis\n", "header")

        # Moving Averages
        self.rec_text.insert(tk.END, "Moving Averages\n", "bold")
        self.rec_text.insert(tk.END, f"• 20-Day SMA: ${sma_20:.2f} ")
        tag = "positive" if current_price > sma_20 else "negative"
        self.rec_text.insert(tk.END, f"({'Above' if current_price > sma_20 else 'Below'} current price)\n", tag)

        self.rec_text.insert(tk.END, f"• 50-Day SMA: ${sma_50:.2f} ")
        tag = "positive" if current_price > sma_50 else "negative"
        self.rec_text.insert(tk.END, f"({'Above' if current_price > sma_50 else 'Below'} current price)\n\n", tag)

        # Momentum Indicators
        self.rec_text.insert(tk.END, "Momentum Indicators\n", "bold")
        self.rec_text.insert(tk.END, f"• RSI (14): {rsi:.2f} ")
        if rsi > 70:
            self.rec_text.insert(tk.END, "(Overbought)\n\n", "negative")
        elif rsi < 30:
            self.rec_text.insert(tk.END, "(Oversold)\n\n", "positive")
        else:
            self.rec_text.insert(tk.END, "(Neutral)\n\n", "neutral")

        # Volatility Indicators
        self.rec_text.insert(tk.END, "Volatility Indicators\n", "bold")
        self.rec_text.insert(tk.END, "• Bollinger Bands:\n")
        self.rec_text.insert(tk.END, f"  - Upper Band: ${upper_bb.iloc[-1]:.2f}\n")
        self.rec_text.insert(tk.END, f"  - Middle Band: ${middle_bb.iloc[-1]:.2f}\n")
        self.rec_text.insert(tk.END, f"  - Lower Band: ${lower_bb.iloc[-1]:.2f}\n")

        # Format volatility with color
        self.rec_text.insert(tk.END, "• Annualized Volatility: ")
        if volatility > 30:
            self.rec_text.insert(tk.END, f"{volatility:.2f}% (High)\n\n", "negative")
        elif volatility > 15:
            self.rec_text.insert(tk.END, f"{volatility:.2f}% (Moderate)\n\n", "neutral")
        else:
            self.rec_text.insert(tk.END, f"{volatility:.2f}% (Low)\n\n", "positive")

        # Volume Analysis
        self.rec_text.insert(tk.END, "Volume Analysis\n", "bold")
        self.rec_text.insert(tk.END, f"• Current Volume: {latest_volume:,.0f}\n")
        self.rec_text.insert(tk.END, f"• 20-Day Average Volume: {volume_avg:,.0f}\n")

        # Format volume ratio with color
        self.rec_text.insert(tk.END, "• Volume Ratio: ")
        if volume_ratio > 1.2:
            self.rec_text.insert(tk.END, f"{volume_ratio:.2f}x (Above Average)\n\n", "positive")
        elif volume_ratio < 0.8:
            self.rec_text.insert(tk.END, f"{volume_ratio:.2f}x (Below Average)\n\n", "negative")
        else:
            self.rec_text.insert(tk.END, f"{volume_ratio:.2f}x (Near Average)\n\n", "neutral")

        # Reasoning
        self.rec_text.insert(tk.END, "Reasoning\n", "header")
        for reason in reasoning:
            self.rec_text.insert(tk.END, f"• {reason}\n")
        self.rec_text.insert(tk.END, "\n")

        # Risk Assessment
        self.rec_text.insert(tk.END, "Risk Assessment\n", "header")

        # Volatility risk
        volatility_desc = "high" if volatility > 30 else "moderate" if volatility > 15 else "low"
        self.rec_text.insert(tk.END,
                             f"• This stock has shown {volatility_desc} volatility with an annualized value of {volatility:.2f}%.\n\n")

        # Volume insight
        if volume_ratio > 1.2:
            self.rec_text.insert(tk.END,
                                 "• Recent trading volume is above average, which may indicate increased investor interest.\n\n")
        elif volume_ratio < 0.8:
            self.rec_text.insert(tk.END,
                                 "• Recent trading volume is below average, which may indicate decreased investor interest.\n\n")
        else:
            self.rec_text.insert(tk.END, "• Recent trading volume is near the average.\n\n")

        # Disclaimer
        self.rec_text.insert(tk.END, "Disclaimer\n", "header")
        disclaimer_text = "This recommendation is based solely on technical analysis and does not take into account " \
                          "fundamental factors such as company financials, industry trends, or economic conditions. " \
                          "This is not financial advice. Always conduct your own research before making investment decisions."
        self.rec_text.insert(tk.END, disclaimer_text)

        self.rec_text.config(state=tk.DISABLED)  # Make it read-only again

    def show_section(self, section):
        """Switch between different views (overview, historical, recommendation)"""
        # Update active button style
        for key, button in self.nav_buttons.items():
            if key == section:
                button.configure(style="Active.Nav.TButton")
            else:
                button.configure(style="Nav.TButton")

        # Hide all frames
        for frame in self.content_frames.values():
            frame.pack_forget()

        # Show the selected frame
        self.content_frames[section].pack(fill=tk.BOTH, expand=True)

        # Update current view
        self.current_view = section

        # If showing historical data, update the historical chart
        if section == "historical" and self.current_stock:
            self.update_historical_data()

        # If showing recommendation, update the recommendation
        if section == "recommendation" and self.current_stock:
            self.update_recommendation()


def main():
    root = tk.Tk()
    app = FinancialAnalyticsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()