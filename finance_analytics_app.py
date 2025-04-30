import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QCheckBox, QFrame, QTableWidget, QTableWidgetItem,
                             QTabWidget, QSplitter, QGroupBox, QGridLayout,
                             QTextEdit, QHeaderView)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QFont
import pyqtgraph as pg

# 样式设置
STYLE = """
QMainWindow {
    background-color: #f0f2f5;
}
QLabel {
    font-size: 12px;
}
QLabel#titleLabel {
    font-size: 14px;
    font-weight: bold;
    color: #2c3e50;
}
QPushButton {
    background-color: #2980b9;
    color: white;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #3498db;
}
QPushButton:pressed {
    background-color: #1c6ea4;
}
QComboBox {
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    padding: 5px;
    min-width: 6em;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #bdc3c7;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}
QCheckBox {
    font-size: 12px;
}
QTableWidget {
    background-color: white;
    alternate-background-color: #f9f9f9;
    border: 1px solid #dcdcdc;
}
QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}
QTextEdit {
    background-color: white;
    border: 1px solid #dcdcdc;
    font-size: 12px;
}
"""


# 模拟股票数据生成
class StockDataGenerator:
    def __init__(self):
        self.stocks = {
            "阿里巴巴(BABA)": {"code": "BABA", "sector": "电商", "pe": 18.5, "dividend": 0.0},
            "腾讯控股(0700.HK)": {"code": "0700.HK", "sector": "互联网", "pe": 22.3, "dividend": 0.4},
            "中国平安(601318.SH)": {"code": "601318.SH", "sector": "金融保险", "pe": 8.9, "dividend": 4.2},
            "贵州茅台(600519.SH)": {"code": "600519.SH", "sector": "白酒", "pe": 45.2, "dividend": 1.2},
            "美国苹果(AAPL)": {"code": "AAPL", "sector": "科技", "pe": 28.1, "dividend": 0.6},
            "特斯拉(TSLA)": {"code": "TSLA", "sector": "汽车", "pe": 67.8, "dividend": 0.0},
            "中国工商银行(601398.SH)": {"code": "601398.SH", "sector": "银行", "pe": 5.1, "dividend": 6.1},
            "万科A(000002.SZ)": {"code": "000002.SZ", "sector": "房地产", "pe": 7.3, "dividend": 5.2},
            "比亚迪(002594.SZ)": {"code": "002594.SZ", "sector": "汽车", "pe": 56.4, "dividend": 0.2},
            "宁德时代(300750.SZ)": {"code": "300750.SZ", "sector": "新能源", "pe": 62.9, "dividend": 0.1}
        }

    def get_stock_list(self):
        return list(self.stocks.keys())

    def get_stock_info(self, stock_name):
        stock = self.stocks.get(stock_name, {})

        # 生成模拟当前价格和涨跌幅
        base_price = random.uniform(50, 500)
        change_pct = random.uniform(-5, 5)
        prev_close = base_price / (1 + change_pct / 100)

        return {
            "code": stock.get("code", ""),
            "name": stock_name.split("(")[0],
            "sector": stock.get("sector", "未知"),
            "price": round(base_price, 2),
            "change": round(change_pct, 2),
            "prev_close": round(prev_close, 2),
            "open": round(prev_close * (1 + random.uniform(-1, 1) / 100), 2),
            "high": round(base_price * (1 + random.uniform(0, 2) / 100), 2),
            "low": round(base_price * (1 - random.uniform(0, 2) / 100), 2),
            "volume": round(random.uniform(1000000, 50000000)),
            "mkt_cap": round(random.uniform(10000000000, 2000000000000), 2),
            "pe_ratio": stock.get("pe", random.uniform(5, 70)),
            "dividend_yield": stock.get("dividend", random.uniform(0, 6)),
            "52w_high": round(base_price * (1 + random.uniform(5, 20) / 100), 2),
            "52w_low": round(base_price * (1 - random.uniform(10, 30) / 100), 2)
        }

    def generate_historical_data(self, stock_name, days=180):
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
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

    def calculate_indicators(self, data, indicators):
        df = data.copy()

        # 计算移动平均线 MA
        if "MA" in indicators:
            df["MA5"] = df["close"].rolling(window=5).mean()
            df["MA10"] = df["close"].rolling(window=10).mean()
            df["MA20"] = df["close"].rolling(window=20).mean()
            df["MA60"] = df["close"].rolling(window=60).mean()

        # 计算相对强弱指数 RSI
        if "RSI" in indicators:
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()

            rs = avg_gain / avg_loss
            df["RSI"] = 100 - (100 / (1 + rs))

        # 计算布林带 BOLL
        if "BOLL" in indicators:
            df["BOLL_MA20"] = df["close"].rolling(window=20).mean()
            df["BOLL_STD"] = df["close"].rolling(window=20).std()
            df["BOLL_UPPER"] = df["BOLL_MA20"] + 2 * df["BOLL_STD"]
            df["BOLL_LOWER"] = df["BOLL_MA20"] - 2 * df["BOLL_STD"]

        # 计算MACD
        if "MACD" in indicators:
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["MACD_LINE"] = exp1 - exp2
            df["MACD_SIGNAL"] = df["MACD_LINE"].ewm(span=9, adjust=False).mean()
            df["MACD_HIST"] = df["MACD_LINE"] - df["MACD_SIGNAL"]

        # KDJ 指标
        if "KDJ" in indicators:
            low_min = df["low"].rolling(window=9).min()
            high_max = df["high"].rolling(window=9).max()

            df["RSV"] = (df["close"] - low_min) / (high_max - low_min) * 100
            df["K"] = df["RSV"].ewm(alpha=1 / 3, adjust=False).mean()
            df["D"] = df["K"].ewm(alpha=1 / 3, adjust=False).mean()
            df["J"] = 3 * df["K"] - 2 * df["D"]

        # 填充NaN值
        df = df.fillna(0)

        return df

    def generate_investment_advice(self, stock_name, data):
        """生成投资建议"""
        df = data.copy()

        if len(df) < 20:
            return "数据不足，无法提供投资建议。"

        # 计算指标
        indicators_df = self.calculate_indicators(df, ["MA", "RSI", "BOLL", "MACD", "KDJ"])

        # 获取最近的指标值
        latest = indicators_df.iloc[-1]
        prev = indicators_df.iloc[-2]

        # 趋势判断
        price_trend = "上升" if latest["close"] > latest["MA20"] else "下降"

        ma_cross_up = (prev["MA5"] <= prev["MA20"]) and (latest["MA5"] > latest["MA20"])
        ma_cross_down = (prev["MA5"] >= prev["MA20"]) and (latest["MA5"] < latest["MA20"])

        # RSI判断
        rsi_value = latest["RSI"] if "RSI" in latest else 0
        rsi_status = "超买" if rsi_value > 70 else "超卖" if rsi_value < 30 else "中性"

        # MACD判断
        macd_cross_up = (prev["MACD_LINE"] <= prev["MACD_SIGNAL"]) and (
                    latest["MACD_LINE"] > latest["MACD_SIGNAL"]) if "MACD_LINE" in latest else False
        macd_cross_down = (prev["MACD_LINE"] >= prev["MACD_SIGNAL"]) and (
                    latest["MACD_LINE"] < latest["MACD_SIGNAL"]) if "MACD_LINE" in latest else False

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
            diff = latest["MACD_LINE"] - latest["MACD_SIGNAL"] if "MACD_LINE" in latest else 0
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
        if latest["close"] > latest["MA20"]:
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
        if latest["close"] < latest["MA20"]:
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


# 主应用窗口
class FinanceAnalyticsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_generator = StockDataGenerator()
        self.current_stock = None
        self.historical_data = None
        self.selected_indicators = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle('金融数据分析软件')
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet(STYLE)

        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QHBoxLayout(main_widget)

        # 左侧控制面板
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)

        # 添加标题
        title_label = QLabel("金融数据分析软件")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        left_layout.addWidget(title_label)

        # 添加股票选择按钮和下拉菜单
        stock_group = QGroupBox("股票选择")
        stock_layout = QVBoxLayout()

        self.stock_button = QPushButton("选择股票")
        self.stock_combo = QComboBox()
        self.stock_combo.addItems(self.data_generator.get_stock_list())
        self.stock_combo.setVisible(False)

        stock_layout.addWidget(self.stock_button)
        stock_layout.addWidget(self.stock_combo)
        stock_group.setLayout(stock_layout)
        left_layout.addWidget(stock_group)

        # 添加技术指标选择组
        indicator_group = QGroupBox("技术指标")
        indicator_layout = QVBoxLayout()

        self.indicator_checks = {}
        for indicator in ["MA", "RSI", "BOLL", "MACD", "KDJ", "Volume"]:
            checkbox = QCheckBox(indicator)
            self.indicator_checks[indicator] = checkbox
            indicator_layout.addWidget(checkbox)

        indicator_group.setLayout(indicator_layout)
        left_layout.addWidget(indicator_group)

        # 添加功能按钮
        function_group = QGroupBox("功能")
        function_layout = QVBoxLayout()

        self.historical_button = QPushButton("历史数据")
        self.investment_advice_button = QPushButton("投资建议")

        function_layout.addWidget(self.historical_button)
        function_layout.addWidget(self.investment_advice_button)
        function_group.setLayout(function_layout)
        left_layout.addWidget(function_group)

        # 添加弹性空间
        left_layout.addStretch()

        # 右侧显示区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 股票信息显示区
        self.stock_info_widget = QWidget()
        self.stock_info_layout = QGridLayout(self.stock_info_widget)
        right_layout.addWidget(self.stock_info_widget)

        # 图表显示区
        self.chart_widget = pg.GraphicsLayoutWidget()
        self.chart_widget.setBackground('w')
        right_layout.addWidget(self.chart_widget)

        # 表格/文本显示区
        self.table_text_widget = QTabWidget()
        self.data_table = QTableWidget()
        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)

        self.table_text_widget.addTab(self.data_table, "数据表")
        self.table_text_widget.addTab(self.advice_text, "投资建议")
        right_layout.addWidget(self.table_text_widget)

        # 设置布局比例
        right_layout.setStretch(0, 1)  # 股票信息区
        right_layout.setStretch(1, 4)  # 图表区
        right_layout.setStretch(2, 2)  # 表格/文本区

        # 添加左右面板到主布局
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        # 连接信号和槽
        self.stock_button.clicked.connect(self.toggle_stock_combo)
        self.stock_combo.currentIndexChanged.connect(self.on_stock_selected)

        for checkbox in self.indicator_checks.values():
            checkbox.stateChanged.connect(self.update_indicators)

        self.historical_button.clicked.connect(self.show_historical_data)
        self.investment_advice_button.clicked.connect(self.show_investment_advice)

    def toggle_stock_combo(self):
        self.stock_combo.setVisible(not self.stock_combo.isVisible())

    def on_stock_selected(self, index):
        if index >= 0:
            stock_name = self.stock_combo.currentText()
            self.current_stock = stock_name
            self.load_stock_data(stock_name)

            # 隐藏下拉菜单
            self.stock_combo.setVisible(False)

    def load_stock_data(self, stock_name):
        # 获取股票信息
        stock_info = self.data_generator.get_stock_info(stock_name)

        # 获取历史数据
        self.historical_data = self.data_generator.generate_historical_data(stock_name)

        # 显示股票信息
        self.display_stock_info(stock_info)

        # 显示历史数据图表
        self.update_chart()

        # 更新数据表格
        self.update_data_table()

    def display_stock_info(self, info):
        # 清除原有内容
        for i in reversed(range(self.stock_info_layout.count())):
            self.stock_info_layout.itemAt(i).widget().setParent(None)

        # 添加股票基本信息
        row, col = 0, 0
        for label, value in [
            ("名称:", info["name"]),
            ("代码:", info["code"]),
            ("行业:", info["sector"]),
            ("当前价:", f"{info['price']:.2f}"),
            ("涨跌幅:", f"{info['change']:.2f}%"),
            ("开盘价:", f"{info['open']:.2f}"),
            ("最高价:", f"{info['high']:.2f}"),
            ("最低价:", f"{info['low']:.2f}"),
            ("成交量:", f"{info['volume']:,}"),
            ("市值:", f"{info['mkt_cap'] / 1e8:.2f}亿"),
            ("PE比率:", f"{info['pe_ratio']:.2f}"),
            ("股息率:", f"{info['dividend_yield']:.2f}%"),
            ("52周高:", f"{info['52w_high']:.2f}"),
            ("52周低:", f"{info['52w_low']:.2f}"),
        ]:
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            value_widget = QLabel(str(value))

            # 如果是涨跌幅，设置颜色
            if label == "涨跌幅:":
                change = info["change"]
                if change > 0:
                    value_widget.setStyleSheet("color: #27ae60;")  # 绿色
                elif change < 0:
                    value_widget.setStyleSheet("color: #e74c3c;")  # 红色

            self.stock_info_layout.addWidget(label_widget, row, col * 2)
            self.stock_info_layout.addWidget(value_widget, row, col * 2 + 1)

            col += 1
            if col >= 3:  # 每行3组数据
                col = 0
                row += 1

    def update_indicators(self):
        self.selected_indicators = []
        for indicator, checkbox in self.indicator_checks.items():
            if checkbox.isChecked():
                self.selected_indicators.append(indicator)

        # 更新图表
        if self.historical_data is not None:
            self.update_chart()

    def update_chart(self):
        # 清除图表内容
        self.chart_widget.clear()

        if self.historical_data is None or self.current_stock is None:
            return

        # 计算指标
        df = self.data_generator.calculate_indicators(
            self.historical_data, self.selected_indicators
        )

        # 创建日期列表 - 用于x轴
        dates = list(range(len(df)))
        date_axis = pg.AxisItem(orientation='bottom')
        date_ticks = [(i, df.iloc[i]['date']) for i in range(0, len(df), len(df) // 10)]
        date_axis.setTicks([date_ticks])

        # 主K线图
        price_plot = self.chart_widget.addPlot(row=0, col=0, axisItems={'bottom': date_axis})
        price_plot.setTitle(f"{self.current_stock} - 价格走势", color="#2c3e50", size="14pt")
        price_plot.showGrid(x=True, y=True, alpha=0.3)

        # 绘制K线图
        for i in range(len(df)):
            # 确定K线颜色
            if df.iloc[i]['close'] >= df.iloc[i]['open']:
                color = pg.mkBrush('#e74c3c')  # 红色 - 收盘价高于开盘价
            else:
                color = pg.mkBrush('#2ecc71')  # 绿色 - 收盘价低于开盘价

            # 添加K线图形 - 蜡烛图
            bar = pg.BarGraphItem(
                x=[i], height=[df.iloc[i]['high'] - df.iloc[i]['low']],
                width=0.3, brush=color, pen=pg.mkPen('k')
            )
            bar.setPos(i, df.iloc[i]['low'])
            price_plot.addItem(bar)

            # 添加实体
            if df.iloc[i]['close'] >= df.iloc[i]['open']:
                body_low = df.iloc[i]['open']
                body_high = df.iloc[i]['close']
            else:
                body_low = df.iloc[i]['close']
                body_high = df.iloc[i]['open']

            body = pg.BarGraphItem(
                x=[i], height=[body_high - body_low],
                width=0.6, brush=color, pen=pg.mkPen('k')
            )
            body.setPos(i, body_low)
            price_plot.addItem(body)

        # 添加技术指标
        if "MA" in self.selected_indicators:
            if "MA5" in df.columns and not df["MA5"].isnull().all():
                ma5 = pg.PlotDataItem(dates, df["MA5"], pen=pg.mkPen('#3498db', width=1.5), name="MA5")
                price_plot.addItem(ma5)

            if "MA10" in df.columns and not df["MA10"].isnull().all():
                ma10 = pg.PlotDataItem(dates, df["MA10"], pen=pg.mkPen('#9b59b6', width=1.5), name="MA10")
                price_plot.addItem(ma10)

            if "MA20" in df.columns and not df["MA20"].isnull().all():
                ma20 = pg.PlotDataItem(dates, df["MA20"], pen=pg.mkPen('#e67e22', width=1.5), name="MA20")
                price_plot.addItem(ma20)

            if "MA60" in df.columns and not df["MA60"].isnull().all():
                ma60 = pg.PlotDataItem(dates, df["MA60"], pen=pg.mkPen('#f1c40f', width=1.5), name="MA60")
                price_plot.addItem(ma60)

        # 添加布林带
        if "BOLL" in self.selected_indicators:
            if all(x in df.columns for x in ["BOLL_UPPER", "BOLL_MA20", "BOLL_LOWER"]):
                upper = pg.PlotDataItem(dates, df["BOLL_UPPER"], pen=pg.mkPen('#3498db', width=1.5), name="上轨")
                middle = pg.PlotDataItem(dates, df["BOLL_MA20"], pen=pg.mkPen('#9b59b6', width=1.5), name="中轨")
                lower = pg.PlotDataItem(dates, df["BOLL_LOWER"], pen=pg.mkPen('#3498db', width=1.5), name="下轨")

                price_plot.addItem(upper)
                price_plot.addItem(middle)
                price_plot.addItem(lower)

        # 添加图例
        price_plot.addLegend()

        # 添加成交量图
        if "Volume" in self.selected_indicators:
            volume_plot = self.chart_widget.addPlot(row=1, col=0, axisItems={'bottom': date_axis})
            volume_plot.setTitle("成交量", color="#2c3e50")
            volume_plot.showGrid(x=True, y=True, alpha=0.3)

            for i in range(len(df)):
                # 确定成交量柱状图颜色
                if i > 0 and df.iloc[i]['close'] >= df.iloc[i - 1]['close']:
                    color = pg.mkBrush('#e74c3c')  # 红色 - 价格上涨
                else:
                    color = pg.mkBrush('#2ecc71')  # 绿色 - 价格下跌

                volume_bar = pg.BarGraphItem(
                    x=[i], height=[df.iloc[i]['volume']],
                    width=0.6, brush=color
                )
                volume_plot.addItem(volume_bar)

            # 链接X轴
            volume_plot.setXLink(price_plot)

        # 添加RSI图表
        if "RSI" in self.selected_indicators and "RSI" in df.columns:
            rsi_plot = self.chart_widget.addPlot(row=2, col=0, axisItems={'bottom': date_axis})
            rsi_plot.setTitle("RSI", color="#2c3e50")
            rsi_plot.showGrid(x=True, y=True, alpha=0.3)

            # 添加RSI线
            rsi_line = pg.PlotDataItem(dates, df["RSI"], pen=pg.mkPen('#e74c3c', width=1.5), name="RSI")
            rsi_plot.addItem(rsi_line)

            # 添加超买超卖线
            rsi_plot.addLine(y=70, pen=pg.mkPen('#3498db', style=Qt.DashLine))
            rsi_plot.addLine(y=30, pen=pg.mkPen('#3498db', style=Qt.DashLine))

            # 设置Y轴范围
            rsi_plot.setYRange(0, 100)

            # 链接X轴
            rsi_plot.setXLink(price_plot)

        # 添加MACD图表
        if "MACD" in self.selected_indicators and all(
                x in df.columns for x in ["MACD_LINE", "MACD_SIGNAL", "MACD_HIST"]):
            macd_plot = self.chart_widget.addPlot(row=3, col=0, axisItems={'bottom': date_axis})
            macd_plot.setTitle("MACD", color="#2c3e50")
            macd_plot.showGrid(x=True, y=True, alpha=0.3)

            # 添加MACD线和信号线
            macd_line = pg.PlotDataItem(dates, df["MACD_LINE"], pen=pg.mkPen('#3498db', width=1.5), name="MACD")
            signal_line = pg.PlotDataItem(dates, df["MACD_SIGNAL"], pen=pg.mkPen('#e74c3c', width=1.5), name="Signal")
            macd_plot.addItem(macd_line)
            macd_plot.addItem(signal_line)

            # 添加MACD柱状图
            for i in range(len(df)):
                hist_val = df.iloc[i]["MACD_HIST"]
                if hist_val >= 0:
                    color = pg.mkBrush('#e74c3c')  # 红色 - 正值
                else:
                    color = pg.mkBrush('#2ecc71')  # 绿色 - 负值

                hist_bar = pg.BarGraphItem(
                    x=[i], height=[hist_val],
                    width=0.6, brush=color
                )
                macd_plot.addItem(hist_bar)

            # 添加图例
            macd_plot.addLegend()

            # 链接X轴
            macd_plot.setXLink(price_plot)

        # 添加KDJ图表
        if "KDJ" in self.selected_indicators and all(x in df.columns for x in ["K", "D", "J"]):
            kdj_plot = self.chart_widget.addPlot(row=4, col=0, axisItems={'bottom': date_axis})
            kdj_plot.setTitle("KDJ", color="#2c3e50")
            kdj_plot.showGrid(x=True, y=True, alpha=0.3)

            # 添加KDJ线
            k_line = pg.PlotDataItem(dates, df["K"], pen=pg.mkPen('#3498db', width=1.5), name="K")
            d_line = pg.PlotDataItem(dates, df["D"], pen=pg.mkPen('#e74c3c', width=1.5), name="D")
            j_line = pg.PlotDataItem(dates, df["J"], pen=pg.mkPen('#2ecc71', width=1.5), name="J")

            kdj_plot.addItem(k_line)
            kdj_plot.addItem(d_line)
            kdj_plot.addItem(j_line)

            # 添加超买超卖线
            kdj_plot.addLine(y=80, pen=pg.mkPen('#3498db', style=Qt.DashLine))
            kdj_plot.addLine(y=20, pen=pg.mkPen('#3498db', style=Qt.DashLine))

            # 添加图例
            kdj_plot.addLegend()

            # 链接X轴
            kdj_plot.setXLink(price_plot)

    def update_data_table(self):
        if self.historical_data is None:
            return

        df = self.historical_data.copy()

        # 设置表格行数和列数
        self.data_table.setRowCount(len(df))
        self.data_table.setColumnCount(6)  # 日期、开盘、最高、最低、收盘、成交量

        # 设置表头
        self.data_table.setHorizontalHeaderLabels(["日期", "开盘", "最高", "最低", "收盘", "成交量"])

        # 填充数据
        for i in range(len(df)):
            row = df.iloc[i]

            date_item = QTableWidgetItem(row["date"])
            open_item = QTableWidgetItem(f"{row['open']:.2f}")
            high_item = QTableWidgetItem(f"{row['high']:.2f}")
            low_item = QTableWidgetItem(f"{row['low']:.2f}")
            close_item = QTableWidgetItem(f"{row['close']:.2f}")
            volume_item = QTableWidgetItem(f"{row['volume']:,}")

            self.data_table.setItem(i, 0, date_item)
            self.data_table.setItem(i, 1, open_item)
            self.data_table.setItem(i, 2, high_item)
            self.data_table.setItem(i, 3, low_item)
            self.data_table.setItem(i, 4, close_item)
            self.data_table.setItem(i, 5, volume_item)

        # 调整列宽
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_historical_data(self):
        if self.current_stock is not None:
            # 更新图表
            self.update_chart()
            # 切换到数据表选项卡
            self.table_text_widget.setCurrentIndex(0)

    def show_investment_advice(self):
        if self.current_stock is not None and self.historical_data is not None:
            # 生成投资建议
            advice = self.data_generator.generate_investment_advice(
                self.current_stock,
                self.historical_data
            )

            # 显示投资建议
            self.advice_text.setText(advice)

            # 切换到投资建议选项卡
            self.table_text_widget.setCurrentIndex(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceAnalyticsApp()
    window.show()
    sys.exit(app.exec_())