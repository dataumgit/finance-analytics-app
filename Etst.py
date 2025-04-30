import tkinter as tk
from tkinter import ttk, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 完整配色优化
COLORS = {
    "bg_main": "#F3F3F4",
    "card_bg": "#FFFFFF",
    "sidebar": "#2C3E50",
    "sidebar_active": "#3498DB",
    "border": "#E7E7E7",
    "text_primary": "#333333",
    "text_secondary": "#676A6C",
    "positive": "#1AB394",
    "negative": "#ED5565",
    "accent": "#3498DB",
    "header": "#333333"
}

# 生成模拟股票数据

def generate_stock_data(days=90):
    date_range = pd.date_range(datetime.now()-timedelta(days=days), periods=days)
    prices = np.cumprod(1 + np.random.normal(0, 0.01, days)) * 100
    volumes = np.random.randint(1000, 5000, days)
    return pd.DataFrame({"Date": date_range, "Close": prices, "Volume": volumes})

class FinancialAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("金融数据分析软件")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS["bg_main"])

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Arial", size=10)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # 配色风格
        self.style.configure("TFrame", background=COLORS["bg_main"])
        self.style.configure("TLabel", background=COLORS["bg_main"], foreground=COLORS["text_primary"])
        self.style.configure("TButton", background=COLORS["sidebar"], foreground="#FFFFFF")
        self.style.configure("Accent.TButton", background=COLORS["accent"], foreground="#FFFFFF")

        self.create_ui()

    def create_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame, width=200, style='TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        stock_frame = ttk.LabelFrame(left_frame, text="股票选择", padding=10)
        stock_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(stock_frame, text="选择股票:").pack(anchor=tk.W, pady=(0, 5))
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(stock_frame, textvariable=self.stock_var, state="readonly", width=30)
        self.stock_combo['values'] = ["Apple Inc. | AAPL", "Microsoft Corp. | MSFT"]
        self.stock_combo.pack(fill=tk.X)
        self.stock_combo.bind("<<ComboboxSelected>>", self.plot_chart)

        nav_frame = ttk.LabelFrame(left_frame, text="导航", padding=10)
        nav_frame.pack(fill=tk.X)

        for section in ["概览", "历史数据", "投资建议"]:
            ttk.Button(nav_frame, text=section, style="TButton").pack(fill=tk.X, pady=2)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        chart_frame = ttk.LabelFrame(right_frame, text="价格走势图", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def plot_chart(self, event=None):
        data = generate_stock_data()
        self.ax.clear()

        self.ax.plot(data["Date"], data["Close"], color=COLORS["accent"], linewidth=2)
        self.ax.set_facecolor(COLORS["card_bg"])
        self.fig.patch.set_facecolor(COLORS["card_bg"])
        self.ax.grid(color=COLORS["border"])
        self.ax.tick_params(axis='x', colors=COLORS["text_secondary"])
        self.ax.tick_params(axis='y', colors=COLORS["text_secondary"])

        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')

        self.canvas.draw()

def main():
    root = tk.Tk()
    app = FinancialAnalyticsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
