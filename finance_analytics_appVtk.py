import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import datetime
import random
from tkinter.font import Font


class StockDataGenerator:
    """模拟股票数据生成器类"""

    def __init__(self):
        # 股票列表 - 格式为 "公司 | 股票代码"
        self.stocks = [
            "阿里巴巴 | BABA",
            "腾讯控股 | 0700.HK",
            "中国平安 | 601318.SH",
            "贵州茅台 | 600519.SH",
            "美国苹果 | AAPL",
            "特斯拉 | TSLA",
            "中国工商银行 | 601398.SH",
            "万科A | 000002.SZ",
            "比亚迪 | 002594.SZ",
            "宁德时代 | 300750.SZ"
        ]

        # 行业信息
        self.sectors = {
            "BABA": "电商",
            "0700.HK": "互联网",
            "601318.SH": "金融保险",
            "600519.SH": "白酒",
            "AAPL": "科技",
            "TSLA": "汽车",
            "601398.SH": "银行",
            "000002.SZ": "房地产",
            "002594.SZ": "汽车",
            "300750.SZ": "新能源"
        }

    def get_stock_list(self):
        """返回股票列表"""
        return self.stocks

    def get_stock_info(self, stock_option):
        """获取股票基本信息"""
        # 从选项中解析股票信息
        parts = stock_option.split(" | ")
        if len(parts) != 2:
            return None

        company_name = parts[0]
        stock_code = parts[1]
        sector = self.sectors.get(stock_code, "未知")

        # 生成模拟数据
        base_price = random.uniform(50, 500)
        change_pct = random.uniform(-5, 5)
        prev_close = base_price / (1 + change_pct / 100)

        return {
            "code": stock_code,
            "name": company_name,
            "sector": sector,
            "price": round(base_price, 2),
            "change": round(change_pct, 2),
            "prev_close": round(prev_close, 2),
            "open": round(prev_close * (1 + random.uniform(-1, 1) / 100), 2),
            "high": round(base_price * (1 + random.uniform(0, 2) / 100), 2),
            "low": round(base_price * (1 - random.uniform(0, 2) / 100), 2),
            "volume": f"{int(random.uniform(1000000, 50000000)):,}",
            "mkt_cap": f"{round(random.uniform(100, 2000), 2)}亿",
            "pe_ratio": round(random.uniform(5, 70), 2),
            "dividend_yield": f"{round(random.uniform(0, 6), 2)}%",
            "52w_high": round(base_price * (1 + random.uniform(5, 20) / 100), 2),
            "52w_low": round(base_price * (1 - random.uniform(10, 30) / 100), 2)
        }

    def generate_historical_data(self, stock_code, days=180):
        """生成历史交易数据"""
        today = datetime.datetime.now()
        dates = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        dates.reverse()

        # 生成起始价格
        start_price = random.uniform(50, 500)

        # 生成价格序列，使用随机游走
        prices = [start_price]
        for i in range(1, days):
            # 随机游走加入部分趋势
            change = random.normalvariate(0, 1) * start_price * 0.01
            trend = np.sin(i / 30) * start_price * 0.003  # 添加周期性趋势
            new_price = max(prices[-1] + change + trend, 1)  # 确保价格为正
            prices.append(new_price)

        # 生成OHLC和交易量
        data = []
        for i, date in enumerate(dates):
            price = prices[i]
            daily_volatility = price * 0.02  # 2%的日内波动

            # OHLC
            open_price = price * (1 + random.uniform(-0.5, 0.5) / 100)
            high_price = max(price, open_price) * (1 + random.uniform(0, 1) / 100)
            low_price = min(price, open_price) * (1 - random.uniform(0, 1) / 100)
            close_price = price

            # 交易量 - 价格上升时交易量通常更大
            if i > 0:
                price_change = (price - prices[i - 1]) / prices[i - 1]
                volume_factor = 1 + price_change * 5  # 价格变化对交易量的影响
                volume = abs(random.normalvariate(5000000, 2000000) * volume_factor)
            else:
                volume = random.normalvariate(5000000, 2000000)

            data.append({
                "date": date,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": int(volume),
                "adj_close": round(close_price, 2)
            })

        return pd.DataFrame(data)

    def calculate_technical_indicators(self, df, indicators):
        """计算技术指标"""
        result_df = df.copy()

        # 移动平均线 MA
        if "MA" in indicators:
            result_df["MA5"] = result_df["close"].rolling(window=5).mean()
            result_df["MA10"] = result_df["close"].rolling(window=10).mean()
            result_df["MA20"] = result_df["close"].rolling(window=20).mean()
            result_df["MA60"] = result_df["close"].rolling(window=60).mean()

        # 相对强弱指数 RSI
        if "RSI" in indicators:
            delta = result_df["close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()

            rs = avg_gain / avg_loss
            result_df["RSI"] = 100 - (100 / (1 + rs))

        # 布林带 BOLL
        if "BOLL" in indicators:
            result_df["BOLL_MA20"] = result_df["close"].rolling(window=20).mean()
            result_df["BOLL_STD"] = result_df["close"].rolling(window=20).std()
            result_df["BOLL_UPPER"] = result_df["BOLL_MA20"] + 2 * result_df["BOLL_STD"]
            result_df["BOLL_LOWER"] = result_df["BOLL_MA20"] - 2 * result_df["BOLL_STD"]

        # MACD
        if "MACD" in indicators:
            exp1 = result_df["close"].ewm(span=12, adjust=False).mean()
            exp2 = result_df["close"].ewm(span=26, adjust=False).mean()
            result_df["MACD"] = exp1 - exp2
            result_df["SIGNAL"] = result_df["MACD"].ewm(span=9, adjust=False).mean()
            result_df["HIST"] = result_df["MACD"] - result_df["SIGNAL"]

        # KDJ 指标
        if "KDJ" in indicators:
            low_min = result_df["low"].rolling(window=9).min()
            high_max = result_df["high"].rolling(window=9).max()

            result_df["RSV"] = (result_df["close"] - low_min) / (high_max - low_min) * 100
            result_df["K"] = result_df["RSV"].ewm(alpha=1 / 3, adjust=False).mean()
            result_df["D"] = result_df["K"].ewm(alpha=1 / 3, adjust=False).mean()
            result_df["J"] = 3 * result_df["K"] - 2 * result_df["D"]

        # 成交量指标
        if "VOL" in indicators:
            # 计算成交量移动平均
            result_df["VOL_MA5"] = result_df["volume"].rolling(window=5).mean()
            result_df["VOL_MA10"] = result_df["volume"].rolling(window=10).mean()

        # 填充NaN值
        result_df = result_df.fillna(0)

        return result_df

    def generate_investment_advice(self, stock_name, data):
        """生成投资建议"""
        df = data.copy()

        if len(df) < 20:
            return "数据不足，无法提供投资建议。"

        # 计算指标
        indicators_df = self.calculate_technical_indicators(df, ["MA", "RSI", "BOLL", "MACD", "KDJ"])

        # 获取最近的指标值
        latest = indicators_df.iloc[-1]
        prev = indicators_df.iloc[-2]

        # 趋势判断
        price_trend = "上升" if latest["close"] > latest["MA20"] else "下降"

        ma_cross_up = False
        ma_cross_down = False
        if "MA5" in latest and "MA20" in latest:
            ma_cross_up = (prev["MA5"] <= prev["MA20"]) and (latest["MA5"] > latest["MA20"])
            ma_cross_down = (prev["MA5"] >= prev["MA20"]) and (latest["MA5"] < latest["MA20"])

        # RSI判断
        rsi_value = latest["RSI"] if "RSI" in latest else 0
        rsi_status = "超买" if rsi_value > 70 else "超卖" if rsi_value < 30 else "中性"

        # MACD判断
        macd_cross_up = False
        macd_cross_down = False
        if "MACD" in latest and "SIGNAL" in latest:
            macd_cross_up = (prev["MACD"] <= prev["SIGNAL"]) and (latest["MACD"] > latest["SIGNAL"])
            macd_cross_down = (prev["MACD"] >= prev["SIGNAL"]) and (latest["MACD"] < latest["SIGNAL"])

        # 生成建议
        advice = f"{stock_name} 技术分析报告\n\n"
        advice += f"1. 价格趋势分析：\n"
        advice += f"   当前价格: {latest['close']:.2f}, 处于{price_trend}趋势。\n"

        if ma_cross_up:
            advice += f"   短期均线上穿长期均线，可能预示着上升趋势的开始。\n"
        elif ma_cross_down:
            advice += f"   短期均线下穿长期均线，可能预示着下降趋势的开始。\n"

        advice += f"\n2. 强弱指标分析：\n"
        advice += f"   RSI(14): {rsi_value:.2f}, 处于{rsi_status}状态。\n"

        if rsi_value > 70:
            advice += f"   RSI指标显示股票可能处于超买状态，价格可能面临回调风险。\n"
        elif rsi_value < 30:
            advice += f"   RSI指标显示股票可能处于超卖状态，价格可能出现反弹机会。\n"

        advice += f"\n3. MACD指标分析：\n"
        if macd_cross_up:
            advice += f"   MACD金叉形成，可能出现买入信号。\n"
        elif macd_cross_down:
            advice += f"   MACD死叉形成，可能出现卖出信号。\n"
        else:
            diff = latest["MACD"] - latest["SIGNAL"] if "MACD" in latest and "SIGNAL" in latest else 0
            advice += f"   MACD指标差值为{diff:.4f}，尚未形成明确交叉信号。\n"

        advice += f"\n4. 布林带分析：\n"
        if "BOLL_UPPER" in latest and "BOLL_LOWER" in latest:
            if latest["close"] > latest["BOLL_UPPER"]:
                advice += f"   价格突破布林带上轨，可能处于强势上涨状态，但也存在回调风险。\n"
            elif latest["close"] < latest["BOLL_LOWER"]:
                advice += f"   价格突破布林带下轨，可能处于超卖状态，存在反弹机会。\n"
            else:
                advice += f"   价格在布林带内运行，波动性正常。\n"

        advice += f"\n5. 综合建议：\n"
        # 根据多个指标给出综合建议
        bullish_signals = 0
        bearish_signals = 0

        # 计算看涨信号
        if "MA20" in latest and latest["close"] > latest["MA20"]:
            bullish_signals += 1
        if ma_cross_up:
            bullish_signals += 2
        if rsi_value < 30:
            bullish_signals += 1
        if macd_cross_up:
            bullish_signals += 2
        if "BOLL_LOWER" in latest and latest["close"] < latest["BOLL_LOWER"]:
            bullish_signals += 1

        # 计算看跌信号
        if "MA20" in latest and latest["close"] < latest["MA20"]:
            bearish_signals += 1
        if ma_cross_down:
            bearish_signals += 2
        if rsi_value > 70:
            bearish_signals += 1
        if macd_cross_down:
            bearish_signals += 2
        if "BOLL_UPPER" in latest and latest["close"] > latest["BOLL_UPPER"]:
            bearish_signals += 1

        # 给出综合建议
        if bullish_signals > bearish_signals + 2:
            advice += f"   根据技术指标分析，{stock_name}目前呈现较强的买入信号，建议考虑逢低买入。\n"
        elif bearish_signals > bullish_signals + 2:
            advice += f"   根据技术指标分析，{stock_name}目前呈现较强的卖出信号，建议考虑择机减持。\n"
        else:
            advice += f"   根据技术指标分析，{stock_name}目前信号不明确，建议观望或小仓位操作。\n"

        advice += f"\n6. 风险提示：\n"
        advice += f"   本建议基于历史数据和技术分析，不构成投资建议。投资决策请结合基本面分析和宏观经济因素，并注意控制风险。\n"

        return advice


class FinanceAnalyticsApp:
    """金融数据分析软件主类"""

    def __init__(self, root):
        self.root = root
        self.root.title("金融数据分析软件")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # 创建数据生成器
        self.data_generator = StockDataGenerator()

        # 当前选择的股票和数据
        self.current_stock = None
        self.stock_code = None
        self.historical_data = None
        self.selected_indicators = []

        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('default')  # 使用默认主题

        # 修改颜色和风格
        self.style.configure("TButton", foreground="#333333", background="#f0f0f0", font=('Arial', 10))
        self.style.configure("TCheckbutton", font=('Arial', 10))
        self.style.configure("TLabel", font=('Arial', 10))
        self.style.configure("Title.TLabel", font=('Arial', 14, 'bold'))
        self.style.configure("Header.TLabel", font=('Arial', 12, 'bold'))
        self.style.configure("Info.TLabel", font=('Arial', 10))
        self.style.configure("TFrame", background="#f5f5f5")

        # 创建UI布局
        self.create_layout()

        # 绑定事件
        self.bind_events()

    def create_layout(self):
        """创建主布局"""
        # 主框架 - 分为左右两部分
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧控制面板
        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 右侧显示区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 保存框架引用
        self.left_frame = left_frame
        self.right_frame = right_frame

        # 创建左侧控制组件
        self.create_left_panel()

        # 创建右侧显示组件
        self.create_right_panel()

    def create_left_panel(self):
        """创建左侧控制面板"""
        # 添加软件标题
        title_label = ttk.Label(self.left_frame, text="金融数据分析软件", style="Title.TLabel")
        title_label.pack(pady=10)

        # 股票选择区域
        stock_frame = ttk.LabelFrame(self.left_frame, text="股票选择")
        stock_frame.pack(fill=tk.X, padx=5, pady=5)

        # 选择股票按钮
        self.stock_button = ttk.Button(stock_frame, text="选择股票")
        self.stock_button.pack(fill=tk.X, padx=5, pady=5)

        # 股票下拉菜单
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(stock_frame, textvariable=self.stock_var)
        self.stock_combo['values'] = self.data_generator.get_stock_list()
        self.stock_combo.pack(fill=tk.X, padx=5, pady=5)
        self.stock_combo.state(['disabled'])  # 初始禁用状态

        # 技术指标选择区域
        indicator_frame = ttk.LabelFrame(self.left_frame, text="技术指标")
        indicator_frame.pack(fill=tk.X, padx=5, pady=5)

        # 创建技术指标复选框
        self.indicator_vars = {}
        self.indicator_checks = {}

        indicators = [
            ("MA", "移动平均线"),
            ("BOLL", "布林带"),
            ("RSI", "相对强弱指数"),
            ("MACD", "MACD指标"),
            ("KDJ", "KDJ指标"),
            ("VOL", "成交量")
        ]

        for code, name in indicators:
            var = tk.BooleanVar()
            check = ttk.Checkbutton(indicator_frame, text=name, variable=var)
            check.pack(anchor=tk.W, padx=5, pady=2)
            self.indicator_vars[code] = var
            self.indicator_checks[code] = check

        # 功能按钮区域
        function_frame = ttk.LabelFrame(self.left_frame, text="功能")
        function_frame.pack(fill=tk.X, padx=5, pady=5)

        # 历史数据按钮
        self.hist_button = ttk.Button(function_frame, text="历史数据")
        self.hist_button.pack(fill=tk.X, padx=5, pady=5)

        # 投资建议按钮
        self.advice_button = ttk.Button(function_frame, text="投资建议")
        self.advice_button.pack(fill=tk.X, padx=5, pady=5)

    def create_right_panel(self):
        """创建右侧显示面板"""
        # 股票信息显示区域
        self.info_frame = ttk.Frame(self.right_frame)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)

        # 图表显示区域
        self.chart_frame = ttk.Frame(self.right_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 默认显示的图表
        fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 底部标签页 - 用于显示数据表和投资建议
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建数据表格页
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="历史数据")

        # 创建投资建议页
        self.advice_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advice_frame, text="投资建议")

        # 在投资建议页添加文本框
        self.advice_text = scrolledtext.ScrolledText(self.advice_frame)
        self.advice_text.pack(fill=tk.BOTH, expand=True)

    def bind_events(self):
        """绑定事件处理函数"""
        # 选择股票按钮点击事件
        self.stock_button.config(command=self.toggle_stock_combo)

        # 股票选择事件
        self.stock_combo.bind("<<ComboboxSelected>>", self.on_stock_selected)

        # 技术指标选择事件
        for var in self.indicator_vars.values():
            var.trace_add("write", self.on_indicator_changed)

        # 功能按钮事件
        self.hist_button.config(command=self.show_historical_data)
        self.advice_button.config(command=self.show_investment_advice)

    def toggle_stock_combo(self):
        """切换股票下拉菜单状态"""
        if 'disabled' in self.stock_combo.state():
            self.stock_combo.state(['!disabled'])  # 启用下拉菜单
            self.stock_combo.focus_set()  # 设置焦点
        else:
            self.stock_combo.state(['disabled'])  # 禁用下拉菜单

    def on_stock_selected(self, event=None):
        """股票选择事件处理"""
        selected = self.stock_var.get()
        if selected:
            self.current_stock = selected
            parts = selected.split(" | ")
            if len(parts) == 2:
                self.stock_code = parts[1]
                self.load_stock_data()
                self.stock_combo.state(['disabled'])  # 选择后禁用下拉菜单

    def on_indicator_changed(self, *args):
        """技术指标选择变化事件处理"""
        # 更新选中的指标列表
        self.selected_indicators = []
        for code, var in self.indicator_vars.items():
            if var.get():
                self.selected_indicators.append(code)

        # 如果有历史数据且选择了指标，更新图表
        if self.historical_data is not None and self.selected_indicators:
            self.update_chart()

    def load_stock_data(self):
        """加载股票数据"""
        if not self.stock_code:
            return

        # 获取股票信息
        stock_info = self.data_generator.get_stock_info(self.current_stock)
        if not stock_info:
            messagebox.showerror("错误", "无法获取股票信息")
            return

        # 清空现有信息显示区域
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        # 创建信息显示网格
        info_grid = ttk.Frame(self.info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=10)

        # 股票基本信息 - 第一行
        ttk.Label(info_grid, text="名称:", style="Info.TLabel").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=stock_info["name"], style="Info.TLabel").grid(row=0, column=1, padx=5, pady=2,
                                                                                sticky=tk.W)

        ttk.Label(info_grid, text="代码:", style="Info.TLabel").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=stock_info["code"], style="Info.TLabel").grid(row=0, column=3, padx=5, pady=2,
                                                                                sticky=tk.W)

        ttk.Label(info_grid, text="行业:", style="Info.TLabel").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=stock_info["sector"], style="Info.TLabel").grid(row=0, column=5, padx=5, pady=2,
                                                                                  sticky=tk.W)

        # 价格信息 - 第二行
        ttk.Label(info_grid, text="当前价:", style="Info.TLabel").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        price_label = ttk.Label(info_grid, text=f"{stock_info['price']}", style="Info.TLabel")
        price_label.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(info_grid, text="涨跌幅:", style="Info.TLabel").grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        change_label = ttk.Label(info_grid, text=f"{stock_info['change']}%", style="Info.TLabel")
        if stock_info['change'] > 0:
            change_label.config(foreground="red")
        else:
            change_label.config(foreground="green")
        change_label.grid(row=1, column=3, padx=5, pady=2, sticky=tk.W)

        ttk.Label(info_grid, text="成交量:", style="Info.TLabel").grid(row=1, column=4, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=stock_info["volume"], style="Info.TLabel").grid(row=1, column=5, padx=5, pady=2,
                                                                                  sticky=tk.W)

        # 更多信息 - 第三行
        ttk.Label(info_grid, text="开盘价:", style="Info.TLabel").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=f"{stock_info['open']}", style="Info.TLabel").grid(row=2, column=1, padx=5, pady=2,
                                                                                     sticky=tk.W)

        ttk.Label(info_grid, text="最高价:", style="Info.TLabel").grid(row=2, column=2, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=f"{stock_info['high']}", style="Info.TLabel").grid(row=2, column=3, padx=5, pady=2,
                                                                                     sticky=tk.W)

        ttk.Label(info_grid, text="最低价:", style="Info.TLabel").grid(row=2, column=4, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=f"{stock_info['low']}", style="Info.TLabel").grid(row=2, column=5, padx=5, pady=2,
                                                                                    sticky=tk.W)

        # 额外信息 - 第四行
        ttk.Label(info_grid, text="市值:", style="Info.TLabel").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=stock_info["mkt_cap"], style="Info.TLabel").grid(row=3, column=1, padx=5, pady=2,
                                                                                   sticky=tk.W)

        ttk.Label(info_grid, text="PE比率:", style="Info.TLabel").grid(row=3, column=2, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=f"{stock_info['pe_ratio']}", style="Info.TLabel").grid(row=3, column=3, padx=5,
                                                                                         pady=2, sticky=tk.W)

        ttk.Label(info_grid, text="股息率:", style="Info.TLabel").grid(row=3, column=4, padx=5, pady=2, sticky=tk.W)
        ttk.Label(info_grid, text=stock_info["dividend_yield"], style="Info.TLabel").grid(row=3, column=5, padx=5,
                                                                                          pady=2, sticky=tk.W)

        # 获取历史数据
        self.historical_data = self.data_generator.generate_historical_data(self.stock_code)

        # 默认显示K线图
        self.update_chart()

        # 更新数据表格
        self.update_data_table()

    def update_chart(self):
        """更新图表显示"""
        if self.historical_data is None or not self.stock_code:
            return

        # 计算选中的技术指标
        df = self.data_generator.calculate_technical_indicators(
            self.historical_data,
            self.selected_indicators
        )

        # 清除图表框架中的内容
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # 创建新的图表
        fig = Figure(figsize=(8, 6), dpi=100)

        # 确定子图数量
        n_plots = 1  # 至少有一个价格图表

        if "VOL" in self.selected_indicators:
            n_plots += 1

        if "RSI" in self.selected_indicators:
            n_plots += 1

        if "MACD" in self.selected_indicators:
            n_plots += 1

        if "KDJ" in self.selected_indicators:
            n_plots += 1

        # 创建子图
        axs = []
        for i in range(n_plots):
            if i == 0:
                # 第一个子图占据更多空间
                ax = fig.add_subplot(n_plots, 1, i + 1, facecolor='#f5f5f5')
                ax.set_position([0.1, 0.3, 0.8, 0.6])  # 占据60%的高度
            else:
                # 其他子图均匀分布剩余空间
                height_per_plot = 0.2 / (n_plots - 1) if n_plots > 1 else 0.2
                bottom = 0.1 + height_per_plot * (i - 1)
                ax = fig.add_subplot(n_plots, 1, i + 1, facecolor='#f5f5f5')
                ax.set_position([0.1, bottom, 0.8, height_per_plot])

            axs.append(ax)

        # 绘制K线图
        ax_price = axs[0]
        dates = pd.to_datetime(df['date'])

        # 计算价格区间稍微扩大，使得图表更美观
        y_min = df['low'].min() * 0.95
        y_max = df['high'].max() * 1.05

        # 绘制K线
        for i in range(len(df)):
            # 确定K线颜色 - 中国股市传统是红涨绿跌
            if df.iloc[i]['close'] >= df.iloc[i]['open']:
                color = 'red'  # 收盘价高于开盘价
            else:
                color = 'green'  # 收盘价低于开盘价

            # 绘制K线实体
            ax_price.add_patch(plt.Rectangle(
                (i, df.iloc[i]['open']),  # 左下角坐标
                0.6,  # 宽度
                df.iloc[i]['close'] - df.iloc[i]['open'],  # 高度
                fill=True,
                color=color
            ))

            # 绘制上下影线
            ax_price.plot(
                [i + 0.3, i + 0.3],
                [df.iloc[i]['high'], max(df.iloc[i]['open'], df.iloc[i]['close'])],
                color='black', linewidth=1
            )
            ax_price.plot(
                [i + 0.3, i + 0.3],
                [min(df.iloc[i]['open'], df.iloc[i]['close']), df.iloc[i]['low']],
                color='black', linewidth=1
            )

        # 添加移动平均线
        if "MA" in self.selected_indicators:
            if 'MA5' in df.columns and not df['MA5'].isnull().all():
                ax_price.plot(df.index, df['MA5'], color='blue', linewidth=1, label='MA5')
            if 'MA10' in df.columns and not df['MA10'].isnull().all():
                ax_price.plot(df.index, df['MA10'], color='orange', linewidth=1, label='MA10')
            if 'MA20' in df.columns and not df['MA20'].isnull().all():
                ax_price.plot(df.index, df['MA20'], color='purple', linewidth=1, label='MA20')
            if 'MA60' in df.columns and not df['MA60'].isnull().all():
                ax_price.plot(df.index, df['MA60'], color='brown', linewidth=1, label='MA60')

        # 添加布林带
        if "BOLL" in self.selected_indicators:
            if all(x in df.columns for x in ["BOLL_UPPER", "BOLL_MA20", "BOLL_LOWER"]):
                ax_price.plot(df.index, df['BOLL_UPPER'], color='blue', linestyle='--', linewidth=1, label='BOLL上轨')
                ax_price.plot(df.index, df['BOLL_MA20'], color='blue', linewidth=1, label='BOLL中轨')
                ax_price.plot(df.index, df['BOLL_LOWER'], color='blue', linestyle='--', linewidth=1, label='BOLL下轨')

        # 设置价格图表
        ax_price.set_title(f"{self.current_stock} - 价格走势", fontsize=12)
        ax_price.set_ylabel('价格', fontsize=10)
        ax_price.grid(True, linestyle='--', alpha=0.7)
        ax_price.set_xlim(-1, len(df))
        ax_price.set_ylim(y_min, y_max)

        # 设置x轴刻度
        xticks_pos = list(range(0, len(df), len(df) // 10))
        xticks_labels = [df.iloc[i]['date'] for i in xticks_pos]
        ax_price.set_xticks(xticks_pos)
        ax_price.set_xticklabels(xticks_labels, rotation=45)

        # 添加图例
        ax_price.legend(loc='upper left')

        # 绘制成交量图
        plot_index = 1
        if "VOL" in self.selected_indicators:
            ax_vol = axs[plot_index]
            plot_index += 1

            for i in range(len(df)):
                # 确定柱状图颜色
                if df.iloc[i]['close'] >= df.iloc[i]['open']:
                    color = 'red'
                else:
                    color = 'green'

                # 绘制成交量柱状图
                ax_vol.bar(i, df.iloc[i]['volume'], width=0.6, color=color, alpha=0.7)

            # 添加成交量均线
            if 'VOL_MA5' in df.columns and not df['VOL_MA5'].isnull().all():
                ax_vol.plot(df.index, df['VOL_MA5'], color='blue', linewidth=1, label='VOL MA5')
            if 'VOL_MA10' in df.columns and not df['VOL_MA10'].isnull().all():
                ax_vol.plot(df.index, df['VOL_MA10'], color='orange', linewidth=1, label='VOL MA10')

            # 设置成交量图表
            ax_vol.set_title('成交量', fontsize=10)
            ax_vol.set_ylabel('成交量', fontsize=8)
            ax_vol.grid(True, linestyle='--', alpha=0.5)
            ax_vol.set_xlim(-1, len(df))

            # 设置x轴刻度
            ax_vol.set_xticks([])  # 不显示x轴刻度

            # 添加图例
            ax_vol.legend(loc='upper left', fontsize=8)

        # 绘制RSI图
        if "RSI" in self.selected_indicators and 'RSI' in df.columns:
            ax_rsi = axs[plot_index]
            plot_index += 1

            # 绘制RSI线
            ax_rsi.plot(df.index, df['RSI'], color='purple', linewidth=1, label='RSI(14)')

            # 添加超买超卖线
            ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.7)
            ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.7)

            # 设置RSI图表
            ax_rsi.set_title('RSI', fontsize=10)
            ax_rsi.set_ylabel('RSI', fontsize=8)
            ax_rsi.grid(True, linestyle='--', alpha=0.5)
            ax_rsi.set_xlim(-1, len(df))
            ax_rsi.set_ylim(0, 100)

            # 设置x轴刻度
            ax_rsi.set_xticks([])  # 不显示x轴刻度

            # 添加图例
            ax_rsi.legend(loc='upper left', fontsize=8)

        # 绘制MACD图
        if "MACD" in self.selected_indicators and all(x in df.columns for x in ["MACD", "SIGNAL", "HIST"]):
            ax_macd = axs[plot_index]
            plot_index += 1

            # 绘制MACD线和信号线
            ax_macd.plot(df.index, df['MACD'], color='blue', linewidth=1, label='MACD')
            ax_macd.plot(df.index, df['SIGNAL'], color='red', linewidth=1, label='SIGNAL')

            # 绘制MACD柱状图
            for i in range(len(df)):
                hist_val = df.iloc[i]['HIST']
                if hist_val >= 0:
                    color = 'red'
                else:
                    color = 'green'

                ax_macd.bar(i, hist_val, width=0.6, color=color, alpha=0.7)

            # 设置MACD图表
            ax_macd.set_title('MACD', fontsize=10)
            ax_macd.set_ylabel('MACD', fontsize=8)
            ax_macd.grid(True, linestyle='--', alpha=0.5)
            ax_macd.set_xlim(-1, len(df))

            # 设置x轴刻度
            ax_macd.set_xticks([])  # 不显示x轴刻度

            # 添加图例
            ax_macd.legend(loc='upper left', fontsize=8)

        # 绘制KDJ图
        if "KDJ" in self.selected_indicators and all(x in df.columns for x in ["K", "D", "J"]):
            ax_kdj = axs[plot_index]
            plot_index += 1

            # 绘制KDJ线
            ax_kdj.plot(df.index, df['K'], color='blue', linewidth=1, label='K')
            ax_kdj.plot(df.index, df['D'], color='orange', linewidth=1, label='D')
            ax_kdj.plot(df.index, df['J'], color='purple', linewidth=1, label='J')

            # 添加超买超卖线
            ax_kdj.axhline(y=80, color='red', linestyle='--', alpha=0.7)
            ax_kdj.axhline(y=20, color='green', linestyle='--', alpha=0.7)

            # 设置KDJ图表
            ax_kdj.set_title('KDJ', fontsize=10)
            ax_kdj.set_ylabel('KDJ', fontsize=8)
            ax_kdj.grid(True, linestyle='--', alpha=0.5)
            ax_kdj.set_xlim(-1, len(df))

            # 设置x轴刻度
            ax_kdj.set_xticks([])  # 不显示x轴刻度

            # 添加图例
            ax_kdj.legend(loc='upper left', fontsize=8)

        # 创建并显示图表
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 添加工具栏
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame)
        toolbar.update()

    def update_data_table(self):
        """更新数据表格"""
        if self.historical_data is None:
            return

        # 清除原有表格
        for widget in self.data_frame.winfo_children():
            widget.destroy()

        # 设置历史数据表格
        columns = ("日期", "开盘", "最高", "最低", "收盘", "成交量", "调整收盘")

        # 创建表格
        table = ttk.Treeview(self.data_frame, columns=columns, show="headings")

        # 添加表头
        for col in columns:
            table.heading(col, text=col)
            table.column(col, width=100, anchor="center")

        # 添加数据行
        df = self.historical_data.copy()
        for i in range(len(df)):
            row = df.iloc[i]
            values = (
                row["date"],
                f"{row['open']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"{row['close']:.2f}",
                f"{row['volume']:,}",
                f"{row['adj_close']:.2f}"
            )
            table.insert("", "end", values=values)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.data_frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        # 布局
        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_historical_data(self):
        """显示历史数据"""
        if self.historical_data is not None:
            # 切换到历史数据选项卡
            self.notebook.select(0)  # 选择第一个选项卡(历史数据)

    def show_investment_advice(self):
        """显示投资建议"""
        if self.current_stock is None or self.historical_data is None:
            messagebox.showinfo("提示", "请先选择股票")
            return

        # 生成投资建议
        advice = self.data_generator.generate_investment_advice(
            self.current_stock,
            self.historical_data
        )

        # 清除原有文本
        self.advice_text.delete(1.0, tk.END)

        # 显示投资建议
        self.advice_text.insert(tk.END, advice)

        # 切换到投资建议选项卡
        self.notebook.select(1)  # 选择第二个选项卡(投资建议)


def main():
    """程序入口函数"""
    root = tk.Tk()
    app = FinanceAnalyticsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()