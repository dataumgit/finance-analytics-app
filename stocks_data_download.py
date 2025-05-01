# import yfinance as yf
import pandas as pd

# 设置股票代码和日期范围
stock_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'BAC', 'V']  # 股票代码列表
start_date = '2024-05-01'
end_date = '2025-05-01'

excel_filename = "stocks_data.xlsx"
csv_filename = "stocks_data.csv"

def getstockinxlsx():
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # 循环下载每个股票的数据并保存到不同的工作表
        for symbol in stock_symbols:
            stock_data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=True)
            if stock_data.empty:
                print(f"没有找到 {symbol} 在 {start_date} 到 {end_date} 之间的数据。")
                break
            else:
                # 保存每个股票的数据到不同的工作表
                #stock_data['Open'] = stock_data['Open'].astype(float).map(lambda x: f"{x:.2f}")
                stock_data.to_excel(writer, sheet_name=symbol)
                current_price = stock_data['Close'].iloc[-1]  # 获取最后一天的收盘价
                print(f"{symbol} Current Price: {current_price}")
        print(f"数据已保存到 {excel_filename}")
#getstockinxlsx()
def getstockincsv():
    # 下载股票数据
    stock_data = yf.download(stock_symbols, start=start_date, end=end_date, auto_adjust=True)
    # 检查是否获取到数据
    if stock_data.empty:
        print(f"没有找到 {stock_symbols} 在 {start_date} 到 {end_date} 之间的数据。")
    else:
        # 输出当前价格和每日数据
        #current_price = stock_data['Close'].iloc[-1]  # 获取最后一天的收盘价
        #print("Current Price:", current_price)
        #print("\nDaily Open, Close, High, Low, Volume:")
        #print(stock_data[['Open', 'Close', 'High', 'Low', 'Volume']])

        # 保存数据到 CSV 文件
        stock_data.to_csv(csv_filename)
        print(f"\n数据已保存到 {csv_filename}")
#getstockincsv()
'''
# 读取 Excel 文件中的所有工作表
xls = pd.ExcelFile(excel_filename)

# 创建一个字典来存储每个股票的数据
stocks_data = {}

# 循环遍历每个工作表，将数据存储到字典中
for sheet_name in xls.sheet_names:
    stocks_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
    stocks_data[sheet_name] = stocks_data[sheet_name].dropna()

    print(f"读取 {sheet_name} 的数据：")
    print(stocks_data[sheet_name].head())  # 显示每个股票数据的前几行

# 访问特定股票的数据示例
aapl_data = stocks_data['AAPL']
print("AAPL 的数据：")
print(aapl_data)
'''
from datetime import datetime, timedelta
import numpy as np
STOCK_DATA_CACHE = {}
# Get stock data from xlsx_file with error handling
excel_filename = "stocks_data.xlsx"
def get_stock_data_from_xlsx(ticker, days=180):
    try:
        # Check cache first
        if ticker in STOCK_DATA_CACHE:
            return STOCK_DATA_CACHE[ticker]

        xlsx_data = pd.read_excel(excel_filename, sheet_name=ticker)

        # Generate dates
        end_date = datetime.strptime('2025-04-30', '%Y-%m-%d')
        start_date = end_date - timedelta(days=days)
        date_range = pd.bdate_range(start_date, end_date)

        tail_rows = xlsx_data.tail(len(date_range))
        close_data = tail_rows['Close'].astype(float).round(2)
        print(close_data)

        # Create dataframe
        data = pd.DataFrame(index=date_range)

        data['Date'] = date_range
        data['Close'] = tail_rows['Close'].astype(float).round(2).values
        data['Open'] = tail_rows['Open'].astype(float).round(2).values
        data['High'] = tail_rows['High'].astype(float).round(2).values
        data['Low'] = tail_rows['Low'].astype(float).round(2).values

        # Ensure High >= Open, Close and Low <= Open, Close
        data['High'] = np.maximum(data['High'], np.maximum(data['Open'], data['Close']))
        data['Low'] = np.minimum(data['Low'], np.minimum(data['Open'], data['Close']))

        # Generate volume
        data['Volume'] = tail_rows['Volume'].astype('int32').values
        print(data)
        # Store in cache
        STOCK_DATA_CACHE[ticker] = data
        return data
    except Exception as e:
        print(f"Error generating stock data: {e}")
        # Return empty dataframe with same structure in case of error
        empty_data = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        return empty_data


