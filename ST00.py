import tkinter as tk
from tkinter import CURRENT, simpledialog
import yfinance as yf
import os
import threading
from queue import Queue



class AdvancedStockApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Trade")
        self.master.geometry("900x500")
        root.configure(bg="#3f3f3f")  


        # 初始化文件路径
        self.watchlist_file = "自選股.txt"
        self.focus_file = "重點觀察股.txt"
        
        # 加载股票列表
        self.watchlist = self.load_stocks(self.watchlist_file)
        self.focus_list = self.load_stocks(self.focus_file)
        
        # 初始化其他变量
        self.sort_mode = "default"
        self.stock_data = {}
        self.gui_update_queue = Queue()
        
        # 创建界面
        self.create_interface()
        self.update_data()
        self.check_queue()

    def create_interface(self):
        """创建界面组件"""
        # 控制面板
        control_frame = tk.Frame(self.master, bg="#3f3f3f", padx=10, pady=10)
        control_frame.pack(fill=tk.X)

        tk.Button(control_frame, text="新增股票", command=self.add_stock).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="預設排序", command=lambda: self.change_sort("default")).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="漲幅排序", command=lambda: self.change_sort("percent")).pack(side=tk.LEFT, padx=5)

        # 重点观察区
        self.focus_label = tk.Label(self.master, text="★ 觀察區--", font=("微軟正黑體", 12, "bold"), fg="#f0f0f0", bg="black")
        self.focus_label.pack(anchor=tk.W, padx=10)
        self.focus_frame = tk.Frame(self.master, bg="#3f3f3f")
        self.focus_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)

        # 自选股显示区
        self.stock_label = tk.Label(self.master, text="自選股列表--", font=("微軟正黑體", 12, "bold"), fg="#f0f0f0", bg="black")
        self.stock_label.pack(anchor=tk.W, padx=10)
        self.stock_frame = tk.Frame(self.master, bg="#3f3f3f")
        self.stock_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    def load_stocks(self, filename):
        """加载股票列表"""
        if not os.path.exists(filename):
            return []
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def save_stocks(self, filename, stocks):
        """保存股票列表"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(stocks))

    def add_stock(self):
        """添加股票到自选股"""
        code = simpledialog.askstring("新增股票", "輸入股票代碼（例：2330.TW）:")
        if code and code not in self.watchlist and code not in self.focus_list:
            self.watchlist.append(code)
            self.save_stocks(self.watchlist_file, self.watchlist)
            self.update_data()

    def change_sort(self, mode):
        """切换排序模式"""
        self.sort_mode = mode
        self.update_display()

    def fetch_stock_data(self):
        """获取股票数据"""
        all_codes = self.watchlist + self.focus_list
        if not all_codes:
            return {}
        
        try:
            tickers = yf.Tickers(" ".join(all_codes))
            data = {}
            for code in all_codes:
                try:
                    stock = tickers.tickers[code]
                    info = stock.info
                    prev_close = info.get('previousClose', 1)
                    current = info.get('regularMarketPrice', prev_close)
                    change_percent = (current - prev_close) / prev_close * 100
                    data[code] = {
                        "percent": change_percent,
                        "price": current
                    }
                except Exception as e:
                    print(f"獲取 {code} 數據失敗: {str(e)}")
            return data
        except Exception as e:
            print("數據獲取錯誤:", str(e))
            return {}

    def update_data(self):
        """启动数据更新线程"""
        def data_thread():
            new_data = self.fetch_stock_data()
            self.stock_data = new_data
            self.gui_update_queue.put(True)
            self.master.after(60000, self.update_data)  # 1分钟更新

        threading.Thread(target=data_thread, daemon=True).start()

    def check_queue(self):
        """检查队列更新GUI"""
        while not self.gui_update_queue.empty():
            self.gui_update_queue.get()
            self.update_display()
        self.master.after(100, self.check_queue)

    def update_display(self):
        """更新显示区域"""
        # 清空现有内容
        for widget in self.focus_frame.winfo_children():
            widget.destroy()
        for widget in self.stock_frame.winfo_children():
            widget.destroy()

        # 排序处理
        sorted_focus = self.sort_stocks(self.focus_list)
        sorted_watch = self.sort_stocks(self.watchlist)

        # 创建格子布局
        self.create_grid(sorted_focus, self.focus_frame)
        self.create_grid(sorted_watch, self.stock_frame)

    def sort_stocks(self, stock_list):
        """根据当前排序模式排序"""
        if self.sort_mode == "percent":
            return sorted(
                stock_list,
                key=lambda x: -self.stock_data.get(x, {}).get("percent", 0),
                reverse=False
            )
        return stock_list

    def create_grid(self, codes, parent_frame):
        """创建股票格子布局"""
        row = col = 0
        for code in codes:
            if code not in self.stock_data:
                continue
            
            cell = self.create_stock_cell(code, parent_frame)
            cell.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # 绑定左键点击事件
            cell.bind("<Button-1>", lambda e, c=code: self.toggle_stock(c))
            
            col += 1
            if col >= 10:
                col = 0
                row += 1

        # 配置网格权重
        for i in range(10):
            parent_frame.columnconfigure(i, weight=1)
        for j in range(row+1):
            parent_frame.rowconfigure(j, weight=1)

    def create_stock_cell(self, code, parent):
        """创建单个股票格子"""
        data = self.stock_data.get(code, {})
        percent = data.get("percent", 0)
        price = data.get("price", 0)
        color = self.get_color(percent)
        
        cell = tk.Frame(parent,
                      bg="black",
                      borderwidth=1,
                      relief="groove",
                      padx=10,
                      pady=5)

        # 股票代码（带颜色）
        code_label = tk.Label(cell,
                            text=code.split(".")[0],  # 显示简化的股票代码
                            fg=color,
                            bg="black",
                            font=("Arial", 12, "bold"))
        code_label.pack()

        # 股價
        percent_label = tk.Label(cell,
                               text=f"{price:.2f}",
                               fg=color,
                               bg="black",
                               font=("Arial", 10))
        percent_label.pack()

        # 涨跌幅百分比
        percent_label = tk.Label(cell,
                               text=f"{percent:+.2f}%",
                               fg=color,
                               bg="black",
                               font=("Arial", 10, "bold"))
        percent_label.pack()

        return cell

    def toggle_stock(self, code):
        """切换股票所在列表"""
        if code in self.focus_list:
            self.focus_list.remove(code)
            self.watchlist.append(code)
        elif code in self.watchlist:
            self.watchlist.remove(code)
            self.focus_list.append(code)
        
        self.save_stocks(self.watchlist_file, self.watchlist)
        self.save_stocks(self.focus_file, self.focus_list)
        self.update_display()

    def get_color(self, percent):
        """获取颜色规则"""
        if percent > 0.5:
            return "#33FF77"  # 上涨绿色
        elif percent < -0.5:
            return "#FF1919"   # 下跌红色
        return "#f0f0f0"       # 平盘黑色
   

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedStockApp(root)
    root.mainloop()