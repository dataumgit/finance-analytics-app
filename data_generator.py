import pandas as pd
import numpy as np
import datetime
import os


def generate_sample_stock_data(ticker="SAMPLE", days=365, start_date=None, volatility=0.02):
    """
    生成样本股票数据

    参数:
    ticker (str): 股票代码
    days (int): 生成的天数
    start_date (datetime): 开始日期，默认为去年今天
    volatility (float): 波动率

    返回:
    DataFrame: 包含样本数据的DataFrame
    """
    if start_date is None:
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)

    # 生成日期序列
    date_list = [start_date + datetime.timedelta(days=x) for x in range(days)]
    # 仅保留工作日 (周一至周五)
    date_list = [date for date in date_list if date.weekday() < 5]

    # 生成价格数据
    np.random.seed(42)  # 为了可重复性

    # 起始价格
    start_price = 100.0

    # 生成随机价格走势
    change_percentage = np.random.normal(0, volatility, len(date_list))
    price_series = [start_price]

    # 添加趋势和季节性
    trend = np.linspace(0, 0.2, len(date_list))  # 上升趋势
    season = 0.1 * np.sin(np.linspace(0, 4 * np.pi, len(date_list)))  # 季节性波动

    for i in range(1, len(date_list)):
        # 添加趋势和季节性到随机波动中
        pct_change = change_percentage[i] + trend[i] + season[i]
        price_series.append(price_series[-1] * (1 + pct_change))

    # 创建开盘价、最高价、最低价
    close_prices = price_series
    open_prices = [p * (1 + np.random.normal(0, volatility / 3)) for p in close_prices]
    high_prices = [max(o, c) * (1 + abs(np.random.normal(0, volatility / 2)))
                   for o, c in zip(open_prices, close_prices)]
    low_prices = [min(o, c) * (1 - abs(np.random.normal(0, volatility / 2)))
                  for o, c in zip(open_prices, close_prices)]

    # 生成成交量数据
    base_volume = 100000
    volume = [int(base_volume * (1 + np.random.normal(0, 0.3) + 0.1 * abs(pct)))
              for pct in change_percentage]

    # 创建特殊事件（如大幅波动）
    event_indices = np.random.choice(range(20, len(date_list)), 5, replace=False)
    for idx in event_indices:
        # 随机决定是上涨还是下跌
        direction = 1 if np.random.random() > 0.5 else -1
        # 振幅增加
        multiplier = 1 + direction * np.random.uniform(0.03, 0.08)
        close_prices[idx] = close_prices[idx - 1] * multiplier
        # 成交量增加
        volume[idx] = int(volume[idx] * np.random.uniform(1.5, 3.0))
        # 调整高低价
        if direction > 0:
            high_prices[idx] = close_prices[idx] * (1 + np.random.uniform(0.005, 0.02))
            low_prices[idx] = min(open_prices[idx], close_prices[idx]) * (1 - np.random.uniform(0.005, 0.01))
        else:
            high_prices[idx] = max(open_prices[idx], close_prices[idx]) * (1 + np.random.uniform(0.005, 0.01))
            low_prices[idx] = close_prices[idx] * (1 - np.random.uniform(0.005, 0.02))

    # 创建DataFrame
    data = {
        'Date': date_list,
        'Open': open_prices,
        'High': high_prices,
        'Low': low_prices,
        'Close': close_prices,
        'Volume': volume,
        'Ticker': [ticker] * len(date_list)
    }

    df = pd.DataFrame(data)
    return df


def save_sample_data(tickers=None, file_format='csv'):
    """
    生成并保存样本股票数据

    参数:
    tickers (list): 股票代码列表，默认为["AAPL", "MSFT", "GOOGL"]
    file_format (str): 文件格式，'csv'或'excel'
    """
    if tickers is None:
        tickers = ["AAPL", "MSFT", "GOOGL"]

    # 确保数据文件夹存在
    if not os.path.exists("sample_data"):
        os.makedirs("sample_data")

    for ticker in tickers:
        print(f"生成 {ticker} 的样本数据...")
        # 生成稍微不同的数据特征
        volatility = np.random.uniform(0.015, 0.03)
        days = np.random.randint(250, 500)

        df = generate_sample_stock_data(ticker=ticker, days=days, volatility=volatility)

        # 保存数据
        if file_format.lower() == 'csv':
            file_path = f"sample_data/{ticker}_stock_data.csv"
            df.to_csv(file_path, index=False)
        elif file_format.lower() == 'excel':
            file_path = f"sample_data/{ticker}_stock_data.xlsx"
            df.to_excel(file_path, index=False)

        print(f"数据已保存到: {file_path}")


if __name__ == "__main__":
    # 生成CSV数据
    save_sample_data(file_format='csv')

    # 生成Excel数据
    save_sample_data(tickers=["SPY", "QQQ", "DIA"], file_format='excel')

    print("所有样本数据生成完成!")