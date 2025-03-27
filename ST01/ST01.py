import yfinance as yf
import tkinter as tk
from tkinter import ttk
import webbrowser

def load_stock_list(filename):
    """讀取股票代碼列表文件"""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def fetch_stock_data(symbols):
    """獲取股票數據並計算漲跌幅"""
    stock_data = []
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='2d')
            if len(hist) < 2:
                continue
            
            prev_close = hist['Close'].iloc[-2]
            last_close = hist['Close'].iloc[-1]
            change_pct = (last_close - prev_close) / prev_close * 100
            
            stock_data.append({
                'symbol': symbol,
                'prev_close': prev_close,
                'last_close': last_close,
                'change_pct': change_pct
            })
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
    return sorted(stock_data, key=lambda x: x['change_pct'], reverse=True)

def create_gui(stock_data):
    """創建圖形界面"""
    root = tk.Tk()
    root.title("股票漲跌幅排序")
    
    # 創建表格
    tree = ttk.Treeview(root, columns=('Symbol', 'PrevClose', 'LastClose', 'Change%'), show='headings')
    tree.heading('Symbol', text='股票代碼')
    tree.heading('PrevClose', text='前收盤價')
    tree.heading('LastClose', text='最新收盤價')
    tree.heading('Change%', text='漲跌幅(%)')
    
    # 設置列寬
    tree.column('Symbol', width=120, anchor='center')
    tree.column('PrevClose', width=120, anchor='e')
    tree.column('LastClose', width=120, anchor='e')
    tree.column('Change%', width=120, anchor='e')
    
    # 添加數據
    for stock in stock_data:
        tree.insert('', 'end', values=(
            stock['symbol'],
            f"{stock['prev_close']:.2f}",
            f"{stock['last_close']:.2f}",
            f"{stock['change_pct']:.2f}%"
        ))
    
    # 右鍵菜單功能
    def open_chart(event):
        item = tree.identify_row(event.y)
        if item:
            symbol = tree.item(item, 'values')[0]
            url = f"https://finance.yahoo.com/chart/{symbol}"
            webbrowser.open(url)
    
    tree.bind('<Button-3>', open_chart)
    tree.pack(expand=True, fill='both')
    
    root.mainloop()

if __name__ == "__main__":
    # 配置參數
    STOCK_FILE = 'stock_list.txt'  # 自選股列表文件
    
    # 主流程
    symbols = load_stock_list(STOCK_FILE)
    stock_data = fetch_stock_data(symbols)
    create_gui(stock_data)