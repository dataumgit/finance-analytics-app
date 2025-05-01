import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
import sys


class FinanceAnalyticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("金融数据分析软件")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # 数据存储
        self.data = None
        self.selected_indicators = []

        # 创建菜单栏
        self.create_menu()

        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建左边控制面板
        self.control_frame = ttk.LabelFrame(self.main_frame, text="控制面板")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 数据导入区域
        self.data_frame = ttk.LabelFrame(self.control_frame, text="数据导入")
        self.data_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(self.data_frame, text="导入CSV数据", command=self.load_csv_data).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(self.data_frame, text="导入Excel数据", command=self.load_excel_data).pack(fill=tk.X, padx=5, pady=5)

        self.data_info_label = ttk.Label(self.data_frame, text="未加载数据")
        self.data_info_label.pack(fill=tk.X, padx=5, pady=5)

        # 技术指标选择区域
        self.indicators_frame = ttk.LabelFrame(self.control_frame, text="技术指标")
        self.indicators_frame.pack(fill=tk.X, padx=5, pady=5)

        # 添加指标复选框
        self.sma_var = tk.BooleanVar()
        self.rsi_var = tk.BooleanVar()
        self.bb_var = tk.BooleanVar()
        self.macd_var = tk.BooleanVar()
        self.vol_var = tk.BooleanVar()

        ttk.Checkbutton(self.indicators_frame, text="简单移动平均线 (SMA)", variable=self.sma_var).pack(anchor=tk.W,padx=5, pady=2)
        ttk.Checkbutton(self.indicators_frame, text="相对强弱指数 (RSI)", variable=self.rsi_var).pack(anchor=tk.W,padx=5, pady=2)
        ttk.Checkbutton(self.indicators_frame, text="布林带 (Bollinger Bands)", variable=self.bb_var).pack(anchor=tk.W,padx=5,pady=2)
        ttk.Checkbutton(self.indicators_frame, text="MACD", variable=self.macd_var).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(self.indicators_frame, text="成交量分析", variable=self.vol_var).pack(anchor=tk.W, padx=5,pady=2)

        # SMA参数
        self.sma_frame = ttk.LabelFrame(self.indicators_frame, text="SMA参数")
        self.sma_frame.pack(fill=tk.X, padx=5, pady=5)

        self.sma10_var = tk.BooleanVar(value=True)
        self.sma20_var = tk.BooleanVar(value=True)
        self.sma50_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(self.sma_frame, text="10日", variable=self.sma10_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.sma_frame, text="20日", variable=self.sma20_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.sma_frame, text="50日", variable=self.sma50_var).pack(side=tk.LEFT, padx=5)

        # 分析按钮
        ttk.Button(self.control_frame, text="开始分析", command=self.analyze_data).pack(fill=tk.X, padx=5, pady=10)

        # 创建右边图表和结果区域
        self.display_frame = ttk.LabelFrame(self.main_frame, text="分析结果")
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 图表显示区域
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, self.display_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 结果解释区域
        self.result_frame = ttk.LabelFrame(self.display_frame, text="结果解释")
        self.result_frame.pack(fill=tk.X, padx=5, pady=5)

        self.result_text = tk.Text(self.result_frame, height=5, wrap=tk.WORD)
        self.result_text.pack(fill=tk.X, padx=5, pady=5)

        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        # 文件菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="导入CSV数据", command=self.load_csv_data)
        file_menu.add_command(label="导入Excel数据", command=self.load_excel_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menu_bar.add_cascade(label="文件", menu=file_menu)

        # 分析菜单
        analysis_menu = tk.Menu(menu_bar, tearoff=0)
        analysis_menu.add_command(label="开始分析", command=self.analyze_data)
        analysis_menu.add_command(label="清空结果", command=self.clear_results)
        menu_bar.add_cascade(label="分析", menu=analysis_menu)

        # 帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="使用指南", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menu_bar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menu_bar)

    def load_csv_data(self):
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                self.process_loaded_data(file_path)
            except Exception as e:
                messagebox.showerror("错误", f"无法加载CSV文件: {e}")

    def load_excel_data(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                self.data = pd.read_excel(file_path)
                self.process_loaded_data(file_path)
            except Exception as e:
                messagebox.showerror("错误", f"无法加载Excel文件: {e}")

    def process_loaded_data(self, file_path):
        if self.data is not None:
            # 确保数据有日期列
            if 'Date' not in self.data.columns:
                # 尝试将第一列解释为日期
                self.data['Date'] = pd.to_datetime(self.data.iloc[:, 0], errors='coerce')
                self.data.set_index('Date', inplace=True)
            else:
                self.data['Date'] = pd.to_datetime(self.data['Date'], errors='coerce')
                self.data.set_index('Date', inplace=True)

            # 显示数据信息
            file_name = os.path.basename(file_path)
            self.data_info_label.config(text=f"已加载: {file_name}\n行数: {len(self.data)}")
            self.status_bar.config(text=f"已加载数据: {file_name}")

            # 清空之前的结果
            self.clear_results()
        else:
            self.data_info_label.config(text="加载数据失败")

    def analyze_data(self):
        if self.data is None:
            messagebox.showwarning("警告", "请先加载数据")
            return

        # 检查是否有收盘价列
        if 'Close' not in self.data.columns:
            messagebox.showwarning("警告", "数据中没有'Close'列")
            return

        # 清空图表
        self.fig.clear()

        # 创建子图
        ax1 = self.fig.add_subplot(211)  # 价格和指标图表
        ax2 = self.fig.add_subplot(212)  # 成交量图表

        # 绘制收盘价
        ax1.plot(self.data.index, self.data['Close'], label='收盘价', color='black')

        result_text = "分析结果:\n"

        # 计算并绘制选定的指标
        if self.sma_var.get():
            if self.sma10_var.get():
                self.data['SMA10'] = self.data['Close'].rolling(window=10).mean()
                ax1.plot(self.data.index, self.data['SMA10'], label='SMA10', color='blue')

            if self.sma20_var.get():
                self.data['SMA20'] = self.data['Close'].rolling(window=20).mean()
                ax1.plot(self.data.index, self.data['SMA20'], label='SMA20', color='green')

            if self.sma50_var.get():
                self.data['SMA50'] = self.data['Close'].rolling(window=50).mean()
                ax1.plot(self.data.index, self.data['SMA50'], label='SMA50', color='red')

            # 添加SMA分析结果
            result_text += self.analyze_sma()

        if self.rsi_var.get():
            # 计算RSI (14天)
            delta = self.data['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()

            rs = avg_gain / avg_loss
            self.data['RSI'] = 100 - (100 / (1 + rs))

            # 创建RSI子图
            ax_rsi = ax1.twinx()
            ax_rsi.plot(self.data.index, self.data['RSI'], label='RSI', color='purple', alpha=0.5)
            ax_rsi.axhline(y=70, color='r', linestyle='--', alpha=0.3)
            ax_rsi.axhline(y=30, color='g', linestyle='--', alpha=0.3)
            ax_rsi.set_ylim(0, 100)
            ax_rsi.set_ylabel('RSI')

            # 添加RSI分析结果
            result_text += self.analyze_rsi()

        if self.bb_var.get():
            # 计算布林带 (20日, 2标准差)
            self.data['SMA20'] = self.data['Close'].rolling(window=20).mean()
            self.data['STD20'] = self.data['Close'].rolling(window=20).std()
            self.data['Upper'] = self.data['SMA20'] + 2 * self.data['STD20']
            self.data['Lower'] = self.data['SMA20'] - 2 * self.data['STD20']

            ax1.plot(self.data.index, self.data['Upper'], label='上轨', color='darkgreen', linestyle='--')
            ax1.plot(self.data.index, self.data['Lower'], label='下轨', color='darkred', linestyle='--')

            # 添加布林带分析结果
            result_text += self.analyze_bollinger()

        if self.macd_var.get():
            # 计算MACD
            self.data['EMA12'] = self.data['Close'].ewm(span=12, adjust=False).mean()
            self.data['EMA26'] = self.data['Close'].ewm(span=26, adjust=False).mean()
            self.data['MACD'] = self.data['EMA12'] - self.data['EMA26']
            self.data['Signal'] = self.data['MACD'].ewm(span=9, adjust=False).mean()
            self.data['Histogram'] = self.data['MACD'] - self.data['Signal']

            # 绘制MACD (在底部子图)
            ax_macd = ax2.twinx()
            ax_macd.plot(self.data.index, self.data['MACD'], label='MACD', color='blue')
            ax_macd.plot(self.data.index, self.data['Signal'], label='Signal', color='red')

            # 绘制柱状图
            ax_macd.bar(self.data.index, self.data['Histogram'], label='Histogram', color='green', alpha=0.3)
            ax_macd.set_ylabel('MACD')

            # 添加MACD分析结果
            result_text += self.analyze_macd()

        if self.vol_var.get():
            # 检查是否有成交量列
            if 'Volume' in self.data.columns:
                # 计算成交量移动平均线
                self.data['VolMA20'] = self.data['Volume'].rolling(window=20).mean()

                # 绘制成交量
                ax2.bar(self.data.index, self.data['Volume'], label='成交量', color='blue', alpha=0.3)
                ax2.plot(self.data.index, self.data['VolMA20'], label='成交量MA20', color='red')
                ax2.set_ylabel('成交量')

                # 添加成交量分析结果
                result_text += self.analyze_volume()
            else:
                messagebox.showwarning("警告", "数据中没有'Volume'列")

        # 设置图表格式
        ax1.set_title('价格与技术指标')
        ax1.set_ylabel('价格')
        ax1.legend(loc='upper left')
        ax1.grid(True)

        ax2.legend(loc='upper left')
        ax2.grid(True)

        # 格式化x轴日期
        self.fig.autofmt_xdate()

        # 调整布局
        self.fig.tight_layout()

        # 更新画布
        self.canvas.draw()

        # 显示结果文本
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_text)

        # 更新状态栏
        self.status_bar.config(text="分析完成")

    def analyze_sma(self):
        """分析SMA指标"""
        result = "\n-- 移动平均线分析 --\n"

        # 获取最新数据
        recent_data = self.data.iloc[-20:].copy()

        # 检查趋势
        if 'SMA10' in self.data.columns and 'SMA50' in self.data.columns:
            if self.data['SMA10'].iloc[-1] > self.data['SMA50'].iloc[-1]:
                if self.data['SMA10'].iloc[-5] <= self.data['SMA50'].iloc[-5]:
                    result += "短期移动平均线刚刚上穿长期移动平均线，可能是买入信号。\n"
                else:
                    result += "短期移动平均线位于长期移动平均线上方，表明价格在上升趋势中。\n"
            else:
                if self.data['SMA10'].iloc[-5] >= self.data['SMA50'].iloc[-5]:
                    result += "短期移动平均线刚刚下穿长期移动平均线，可能是卖出信号。\n"
                else:
                    result += "短期移动平均线位于长期移动平均线下方，表明价格在下降趋势中。\n"

        return result

    def analyze_rsi(self):
        """分析RSI指标"""
        result = "\n-- RSI分析 --\n"

        if 'RSI' in self.data.columns:
            current_rsi = self.data['RSI'].iloc[-1]

            if current_rsi > 70:
                result += f"当前RSI为{current_rsi:.2f}，处于超买区域，可能预示价格回调。\n"
            elif current_rsi < 30:
                result += f"当前RSI为{current_rsi:.2f}，处于超卖区域，可能预示价格反弹。\n"
            else:
                result += f"当前RSI为{current_rsi:.2f}，在中性区域。\n"

        return result

    def analyze_bollinger(self):
        """分析布林带指标"""
        result = "\n-- 布林带分析 --\n"

        if 'Upper' in self.data.columns and 'Lower' in self.data.columns:
            current_price = self.data['Close'].iloc[-1]
            upper_band = self.data['Upper'].iloc[-1]
            lower_band = self.data['Lower'].iloc[-1]

            band_width = (upper_band - lower_band) / self.data['SMA20'].iloc[-1] * 100

            if current_price > upper_band:
                result += f"价格突破上轨({upper_band:.2f})，可能处于超买状态。\n"
            elif current_price < lower_band:
                result += f"价格突破下轨({lower_band:.2f})，可能处于超卖状态。\n"
            else:
                result += f"价格在布林带通道内({lower_band:.2f} - {upper_band:.2f})。\n"

            if band_width < 10:
                result += "布林带收窄，波动率较低，可能即将迎来较大波动。\n"
            elif band_width > 30:
                result += "布林带扩张，市场波动性较高。\n"

        return result

    def analyze_macd(self):
        """分析MACD指标"""
        result = "\n-- MACD分析 --\n"

        if 'MACD' in self.data.columns and 'Signal' in self.data.columns:
            current_macd = self.data['MACD'].iloc[-1]
            current_signal = self.data['Signal'].iloc[-1]

            if current_macd > current_signal:
                if self.data['MACD'].iloc[-2] <= self.data['Signal'].iloc[-2]:
                    result += "MACD刚刚上穿信号线，这是一个潜在的买入信号。\n"
                else:
                    result += "MACD位于信号线上方，表明上升趋势。\n"
            else:
                if self.data['MACD'].iloc[-2] >= self.data['Signal'].iloc[-2]:
                    result += "MACD刚刚下穿信号线，这是一个潜在的卖出信号。\n"
                else:
                    result += "MACD位于信号线下方，表明下降趋势。\n"

            if current_macd > 0:
                result += "MACD位于零线上方，整体趋势偏向积极。\n"
            else:
                result += "MACD位于零线下方，整体趋势偏向消极。\n"

        return result

    def analyze_volume(self):
        """分析成交量"""
        result = "\n-- 成交量分析 --\n"

        if 'Volume' in self.data.columns and 'VolMA20' in self.data.columns:
            current_vol = self.data['Volume'].iloc[-1]
            avg_vol = self.data['VolMA20'].iloc[-1]

            vol_ratio = current_vol / avg_vol

            if vol_ratio > 2:
                result += "当前成交量显著高于平均值，表明交易活跃度增加。\n"

                # 检查价格变动
                price_change = self.data['Close'].iloc[-1] - self.data['Close'].iloc[-2]
                if price_change > 0:
                    result += "价格上涨伴随大成交量，表明强劲的买入压力。\n"
                else:
                    result += "价格下跌伴随大成交量，表明强劲的卖出压力。\n"
            elif vol_ratio < 0.5:
                result += "当前成交量显著低于平均值，表明交易活跃度减少。\n"
            else:
                result += "当前成交量处于正常范围。\n"

        return result

    def clear_results(self):
        """清空分析结果"""
        # 清空图表
        self.fig.clear()
        self.canvas.draw()

        # 清空结果文本
        self.result_text.delete(1.0, tk.END)

    def show_help(self):
        """显示帮助信息"""
        help_text = """
        金融数据分析软件使用指南

        1. 数据导入:
           - 使用"文件"菜单或控制面板中的按钮导入CSV或Excel格式的股票数据
           - 数据应包含日期、开盘价、最高价、最低价、收盘价和成交量等列

        2. 技术指标:
           - 简单移动平均线(SMA): 反映价格的平均趋势
           - 相对强弱指数(RSI): 衡量价格动量，判断超买超卖
           - 布林带: 显示价格波动范围
           - MACD: 判断中长期趋势转变
           - 成交量分析: 评估市场参与度

        3. 分析过程:
           - 选择需要的技术指标
           - 点击"开始分析"按钮
           - 查看图表和结果解释
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("使用指南")
        help_window.geometry("600x400")

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

    def show_about(self):
        """显示关于信息"""
        about_text = """
        金融数据分析软件

        版本: 1.0

        这是一个用于分析股票数据的应用程序，提供多种技术指标计算和可视化功能。

        支持的技术指标:
        - 简单移动平均线(SMA)
        - 相对强弱指数(RSI)
        - 布林带(Bollinger Bands)
        - MACD
        - 成交量分析

        开发者: ELEC 7078A 项目组
        """

        messagebox.showinfo("关于", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceAnalyticsApp(root)
    root.mainloop()