import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import os
import sys
from datetime import datetime, timedelta

# 设置深色主题颜色
DARK_BG = "#121212"
CARD_BG = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
ACCENT_GREEN = "#4CAF50"
ACCENT_RED = "#F44336"
GRID_COLOR = "#333333"
BORDER_COLOR = "#333333"
HIGHLIGHT_COLOR = "#2979FF"


class ModernFinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("金融数据分析软件")
        self.root.geometry("1280x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg=DARK_BG)

        # 设置字体
        self.title_font = ("Arial", 18, "bold")
        self.header_font = ("Arial", 14, "bold")
        self.normal_font = ("Arial", 12)
        self.small_font = ("Arial", 10)

        # 数据存储
        self.data = None
        self.current_ticker = "AAPL"
        self.current_price = 210.14
        self.price_change = 0.86
        self.price_change_percent = 0.41
        self.prev_close = 209.28
        self.open_price = 210.85
        self.open_change = 0.71
        self.open_change_percent = 0.34

        # 指标数据
        self.eps = 1.62
        self.analyst_rating = "强烈推荐"
        self.price_target = 236.28
        self.min_target = 165.00
        self.max_target = 300.00

        self.quarters = ["Q1'24", "Q2'24", "Q3'24", "Q4'24"]
        self.eps_data = [1.52, 1.55, 1.58, 1.62]
        self.revenue_data = [84.3, 89.5, 94.8, 124.3]
        self.profit_data = [24.2, 28.6, 32.1, 36.3]

        self.analyst_buy = [8, 7, 7, 8]
        self.analyst_hold = [13, 14, 14, 14]
        self.analyst_sell = [5, 4, 4, 4]
        self.analyst_months = ["1月", "2月", "3月", "4月"]

        # 创建主框架
        self.create_header()
        self.create_main_frame()

    def create_header(self):
        """创建顶部标题栏"""
        header_frame = tk.Frame(self.root, bg=DARK_BG, height=100, pady=10)
        header_frame.pack(fill=tk.X)

        # 股票名称和代码
        name_frame = tk.Frame(header_frame, bg=DARK_BG)
        name_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(name_frame, text="Apple Inc. (AAPL)", font=self.title_font, bg=DARK_BG, fg=TEXT_COLOR).pack(
            anchor=tk.W)

        # 当前价格和变化
        price_frame = tk.Frame(header_frame, bg=DARK_BG)
        price_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(price_frame, text=f"{self.current_price:.2f}", font=self.title_font, bg=DARK_BG, fg=TEXT_COLOR).pack(
            side=tk.LEFT)

        change_color = ACCENT_GREEN if self.price_change >= 0 else ACCENT_RED
        change_sign = "+" if self.price_change >= 0 else ""
        tk.Label(price_frame,
                 text=f" {change_sign}{self.price_change:.2f} ({change_sign}{self.price_change_percent:.2f}%)",
                 font=self.header_font, bg=DARK_BG, fg=change_color).pack(side=tk.LEFT)

        # 开盘价和变化
        open_frame = tk.Frame(header_frame, bg=DARK_BG)
        open_frame.pack(side=tk.LEFT, padx=40)

        tk.Label(open_frame, text=f"{self.open_price:.2f}", font=self.title_font, bg=DARK_BG, fg=TEXT_COLOR).pack(
            side=tk.LEFT)

        change_color = ACCENT_GREEN if self.open_change >= 0 else ACCENT_RED
        change_sign = "+" if self.open_change >= 0 else ""
        tk.Label(open_frame,
                 text=f" {change_sign}{self.open_change:.2f} ({change_sign}{self.open_change_percent:.2f}%)",
                 font=self.header_font, bg=DARK_BG, fg=change_color).pack(side=tk.LEFT)

        # 交易信息
        time_frame = tk.Frame(header_frame, bg=DARK_BG)
        time_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(time_frame, text="收市: 下午4:00:03 [EDT]", font=self.small_font, bg=DARK_BG, fg="#AAAAAA").pack(
            anchor=tk.W)
        tk.Label(time_frame, text="开市前: 上午5:39:34 [EDT]", font=self.small_font, bg=DARK_BG, fg="#AAAAAA").pack(
            anchor=tk.W)

        # 右侧开始交易按钮
        trade_button = tk.Button(header_frame, text="开始交易 / Start Trading >>", font=self.normal_font,
                                 bg="#0D47A1", fg=TEXT_COLOR, padx=15, pady=5)
        trade_button.pack(side=tk.RIGHT, padx=20)

    def create_main_frame(self):
        """创建主要内容区域"""
        # 标题
        tk.Label(self.root, text="研究分析", font=self.header_font, bg=DARK_BG, fg=TEXT_COLOR, anchor=tk.W).pack(
            fill=tk.X, padx=20, pady=(20, 10))

        # 主内容框架
        content_frame = tk.Frame(self.root, bg=DARK_BG)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建四个卡片
        self.create_eps_card(content_frame)
        self.create_revenue_profit_card(content_frame)
        self.create_analyst_rating_card(content_frame)
        self.create_price_target_card(content_frame)

        # 盈利预估标题
        tk.Label(self.root, text="盈利预估", font=self.header_font, bg=DARK_BG, fg=TEXT_COLOR, anchor=tk.W).pack(
            fill=tk.X, padx=20, pady=(20, 10))

        # 盈利预估表格
        self.create_earnings_table()

    def create_eps_card(self, parent):
        """创建每股盈利卡片"""
        card = tk.Frame(parent, bg=CARD_BG, padx=10, pady=10, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        tk.Label(card, text="每股盈利", font=self.normal_font, bg=CARD_BG, fg=TEXT_COLOR).pack(anchor=tk.W,
                                                                                               pady=(0, 10))

        # 创建每股盈利图表
        fig = Figure(figsize=(4, 2), dpi=100, facecolor=CARD_BG)
        ax = fig.add_subplot(111)

        # 设置条形图
        bars = ax.bar(self.quarters, self.eps_data, color=ACCENT_GREEN, width=0.6)

        # 在顶部添加beat标签
        for i, bar in enumerate(bars):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    'Beat', ha='center', va='bottom', color=ACCENT_GREEN, fontsize=8)

            # 添加+$0.06这样的标签
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                    f'+US${0.06:.2f}', ha='center', va='bottom', color=ACCENT_GREEN, fontsize=8)

        # 在图表上方添加预估
        ax.text(0.5, 0.9, f"+{self.eps} 预估", transform=ax.transAxes, ha='center', color=ACCENT_GREEN, fontsize=15,
                weight='bold')

        # 设置图表样式
        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors=TEXT_COLOR, which='both')
        ax.spines['bottom'].set_color(GRID_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.grid(False)
        ax.set_ylim(0, max(self.eps_data) * 1.3)  # 给标签留出空间

        # 添加月份标签
        for i, quarter in enumerate(self.quarters):
            ax.text(i, -0.15, quarter, ha='center', va='bottom', color=TEXT_COLOR, fontsize=8)
            date_text = "May 01" if i == len(self.quarters) - 1 else ""
            ax.text(i, -0.3, date_text, ha='center', va='bottom', color=TEXT_COLOR, fontsize=8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_revenue_profit_card(self, parent):
        """创建收益与盈利卡片"""
        card = tk.Frame(parent, bg=CARD_BG, padx=10, pady=10, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        tk.Label(card, text="收益与盈利", font=self.normal_font, bg=CARD_BG, fg=TEXT_COLOR).pack(anchor=tk.W,
                                                                                                 pady=(0, 5))

        # 标签行
        label_frame = tk.Frame(card, bg=CARD_BG)
        label_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(label_frame, text="收益", font=self.small_font, bg=CARD_BG, fg="#42A5F5").pack(side=tk.LEFT)
        tk.Label(label_frame, text=f"{self.revenue_data[-1]}十亿", font=self.small_font, bg=CARD_BG, fg="#42A5F5").pack(
            side=tk.LEFT, padx=(5, 20))

        tk.Label(label_frame, text="盈利", font=self.small_font, bg=CARD_BG, fg="#FFA000").pack(side=tk.LEFT)
        tk.Label(label_frame, text=f"{self.profit_data[-1]}十亿", font=self.small_font, bg=CARD_BG, fg="#FFA000").pack(
            side=tk.LEFT, padx=5)

        # 创建收益与盈利图表
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=CARD_BG)
        ax = fig.add_subplot(111)

        # 设置柱状图
        bar_width = 0.35
        x = np.arange(len(self.quarters))

        # 收益柱状图（蓝色）
        revenue_bars = ax.bar(x - bar_width / 2, self.revenue_data, bar_width, color='#42A5F5', label='收益')

        # 盈利柱状图（黄色）
        profit_bars = ax.bar(x + bar_width / 2, self.profit_data, bar_width, color='#FFA000', label='盈利')

        # 设置图表样式
        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors=TEXT_COLOR, which='both')
        ax.spines['bottom'].set_color(GRID_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_xticks(x)
        ax.set_xticklabels([f"Q{i + 1}'24" for i in range(4)])
        ax.grid(True, axis='y', linestyle='--', color=GRID_COLOR, alpha=0.3)

        # 设置Y轴刻度
        max_revenue = max(self.revenue_data)
        ax.set_yticks(np.arange(0, max_revenue * 1.2, 20))

        # 左侧添加标签
        ax.text(-0.1, 0.5, "120B\n100B\n80B\n60B\n40B\n20B\n0", transform=ax.transAxes,
                va='center', ha='right', color=TEXT_COLOR, fontsize=8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_analyst_rating_card(self, parent):
        """创建分析师建议卡片"""
        card = tk.Frame(parent, bg=CARD_BG, padx=10, pady=10, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        tk.Label(card, text="分析师建议", font=self.normal_font, bg=CARD_BG, fg=TEXT_COLOR).pack(anchor=tk.W,
                                                                                                 pady=(0, 10))

        # 创建图例
        legend_frame = tk.Frame(card, bg=CARD_BG)
        legend_frame.pack(fill=tk.X, pady=(0, 5))

        # 颜色对应的标签
        colors = [('#00C853', '强烈推荐'), ('#8BC34A', '买入'), ('#FFD600', '持有'),
                  ('#FF9800', '落后大市'), ('#F44336', '卖出')]

        for color, label in colors:
            dot = tk.Canvas(legend_frame, width=10, height=10, bg=CARD_BG, highlightthickness=0)
            dot.create_oval(2, 2, 8, 8, fill=color, outline="")
            dot.pack(side=tk.LEFT, padx=(0, 5))

            tk.Label(legend_frame, text=label, font=self.small_font, bg=CARD_BG, fg=TEXT_COLOR).pack(side=tk.LEFT,
                                                                                                     padx=(0, 15))

        # 创建分析师建议图表
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=CARD_BG)
        ax = fig.add_subplot(111)

        # 堆叠柱状图数据
        months = self.analyst_months
        buy_data = self.analyst_buy
        hold_data = self.analyst_hold
        sell_data = self.analyst_sell

        # 计算总分析师数
        total_analysts = [b + h + s for b, h, s in zip(buy_data, hold_data, sell_data)]

        # 绘制堆叠柱状图
        width = 0.6
        buy_bars = ax.bar(months, buy_data, width, label='买入', color='#8BC34A')
        hold_bars = ax.bar(months, hold_data, width, bottom=buy_data, label='持有', color='#FFD600')

        # 计算卖出部分的底部位置
        sell_bottom = [b + h for b, h in zip(buy_data, hold_data)]
        sell_bars = ax.bar(months, sell_data, width, bottom=sell_bottom, label='卖出', color='#F44336')

        # 在柱子顶部添加总数
        for i, total in enumerate(total_analysts):
            ax.text(i, total + 1, str(total), ha='center', va='bottom', color=TEXT_COLOR)

        # 在柱子中间添加分析师数量
        for i, (b, h, s) in enumerate(zip(buy_data, hold_data, sell_data)):
            # 买入数量
            if b > 0:
                ax.text(i, b / 2, str(b), ha='center', va='center', color='white')

            # 持有数量
            if h > 0:
                ax.text(i, b + h / 2, str(h), ha='center', va='center', color='black')

            # 卖出数量
            if s > 0:
                ax.text(i, b + h + s / 2, str(s), ha='center', va='center', color='white')

        # 设置图表样式
        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors=TEXT_COLOR, which='both')
        ax.spines['bottom'].set_color(GRID_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_ylim(0, max(total_analysts) * 1.15)  # 给标签留出空间
        ax.grid(False)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_price_target_card(self, parent):
        """创建分析师目标价卡片"""
        card = tk.Frame(parent, bg=CARD_BG, padx=10, pady=10, highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        tk.Label(card, text="分析师目标价", font=self.normal_font, bg=CARD_BG, fg=TEXT_COLOR).pack(anchor=tk.W,
                                                                                                   pady=(0, 10))

        # 目标价图表
        fig = Figure(figsize=(4, 2.5), dpi=100, facecolor=CARD_BG)
        ax = fig.add_subplot(111)

        # 价格区间
        min_price = self.min_target
        current_price = self.current_price
        target_price = self.price_target
        max_price = self.max_target

        # 绘制水平价格线
        ax.axhline(y=0, color=GRID_COLOR, linewidth=1)

        # 价格区间线
        ax.plot([0, 1], [0, 0], color=HIGHLIGHT_COLOR, linewidth=3)

        # 标记点
        # 最低价
        ax.scatter(0.1, 0, color=TEXT_COLOR, s=40, zorder=5)
        ax.text(0.1, 0.15, f"{min_price:.2f}\n最低", ha='center', va='bottom', color=TEXT_COLOR, fontsize=8)

        # 目标价
        ax.scatter(0.5, 0, color=HIGHLIGHT_COLOR, s=50, zorder=5)
        ax.text(0.5, 0.15, f"{target_price:.2f}\n平均", ha='center', va='bottom', color=HIGHLIGHT_COLOR, fontsize=10,
                weight='bold')

        # 当前价
        ax.scatter(current_price / max_price * 0.9, 0, color='white', s=40, zorder=5, edgecolors=HIGHLIGHT_COLOR,
                   linewidth=2)
        ax.text(current_price / max_price * 0.9, -0.15, f"{current_price:.2f}\n目前", ha='center', va='top',
                color='white', fontsize=8)

        # 最高价
        ax.scatter(0.9, 0, color=TEXT_COLOR, s=40, zorder=5)
        ax.text(0.9, 0.15, f"{max_price:.2f}\n最高", ha='center', va='bottom', color=TEXT_COLOR, fontsize=8)

        # 设置图表样式
        ax.set_facecolor(CARD_BG)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        ax.axis('off')  # 隐藏坐标轴

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_earnings_table(self):
        """创建盈利预估表格"""
        table_frame = tk.Frame(self.root, bg=DARK_BG, padx=20, pady=10)
        table_frame.pack(fill=tk.X, padx=20, pady=10)

        # 创建表格
        columns = ["分析师数目", "平均预估", "低估", "高估"]
        periods = ["本季 (2025年3月)", "下一季 (2025年6月)", "本年度 (2025年)", "下一年 (2026年)"]

        # 创建表头
        header_frame = tk.Frame(table_frame, bg=DARK_BG)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        # 货币标签
        tk.Label(header_frame, text="货币为USD", font=self.small_font, bg=DARK_BG, fg=TEXT_COLOR, anchor=tk.W).pack(
            side=tk.LEFT)

        # 创建表格标题行
        title_frame = tk.Frame(table_frame, bg=DARK_BG)
        title_frame.pack(fill=tk.X)

        # 添加空白列
        tk.Label(title_frame, text="", width=25, font=self.normal_font, bg=DARK_BG, fg=TEXT_COLOR, anchor=tk.W).pack(
            side=tk.LEFT)

        # 添加列标题
        for period in periods:
            tk.Label(title_frame, text=period, width=20, font=self.normal_font, bg=DARK_BG, fg=TEXT_COLOR,
                     anchor=tk.CENTER).pack(side=tk.LEFT)

        # 创建表格数据部分
        table_data = [
            ["分析师数目", "26", "24", "40", "39"],
            ["平均预估", "1.62", "1.47", "7.25", "7.97"],
            ["低估", "1.5", "1.25", "6.68", "6.95"],
            ["高估", "1.66", "1.55", "7.7", "9"]
        ]

        # 创建分隔线
        separator = tk.Frame(table_frame, height=1, bg=BORDER_COLOR)
        separator.pack(fill=tk.X, pady=5)

        # 添加表格数据行
        for row_data in table_data:
            row_frame = tk.Frame(table_frame, bg=DARK_BG)
            row_frame.pack(fill=tk.X, pady=5)

            # 行标题
            tk.Label(row_frame, text=row_data[0], width=25, font=self.normal_font, bg=DARK_BG, fg=TEXT_COLOR,
                     anchor=tk.W).pack(side=tk.LEFT)

            # 行数据
            for cell in row_data[1:]:
                tk.Label(row_frame, text=cell, width=20, font=self.normal_font, bg=DARK_BG, fg=TEXT_COLOR,
                         anchor=tk.CENTER).pack(side=tk.LEFT)

    def load_data(self, file_path=None):
        """加载数据"""
        if file_path is None:
            file_path = filedialog.askopenfilename(
                title="选择数据文件",
                filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
            )

        if not file_path:
            return

        try:
            # 根据文件类型加载数据
            if file_path.endswith(('.xlsx', '.xls')):
                self.data = pd.read_excel(file_path)
            else:
                self.data = pd.read_csv(file_path)

            # 处理数据
            self.process_data()
            messagebox.showinfo("加载成功", f"成功加载数据: {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("错误", f"无法加载数据: {e}")

    def process_data(self):
        """处理加载的数据"""
        if self.data is None:
            return

        # 这里可以添加数据处理逻辑
        # 例如计算技术指标、提取关键数据等
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernFinanceApp(root)

    # 设置列权重，使卡片均匀分布
    for i in range(4):
        root.columnconfigure(i, weight=1)

    root.mainloop()