class LinearRegression:
    def __init__(self):
        """初始化線性回歸計算器"""
        self.points = []  # 儲存 (x, y) 點
        self.slope = None      # 斜率
        self.intercept = None  # y 軸截距
    
    def add_point(self, x, y):
        """新增一個 (x, y) 點"""
        self.points.append((x, y))
        # 當有新點加入時，清除之前計算的回歸參數
        self.slope = None
        self.intercept = None
        print(f"已新增點: ({x}, {y})")
    
    def add_points(self, points_list):
        """批量新增多個點"""
        for x, y in points_list:
            self.points.append((x, y))
        self.slope = None
        self.intercept = None
        print(f"已新增 {len(points_list)} 個點")
    
    def get_points_count(self):
        """取得目前點的數量"""
        return len(self.points)
    
    def calculate_regression(self):
        """計算線性回歸參數（斜率和截距）"""
        if len(self.points) < 2:
            raise ValueError("需要至少 2 個點才能進行線性回歸")
        
        # 取得所有 x 和 y 值
        x_values = [point[0] for point in self.points]
        y_values = [point[1] for point in self.points]
        
        n = len(self.points)
        
        # 計算平均值
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # 計算斜率 (slope)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in self.points)
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            raise ValueError("無法計算線性回歸：所有 x 值相同")
        
        self.slope = numerator / denominator
        
        # 計算 y 軸截距 (intercept)
        self.intercept = y_mean - self.slope * x_mean
        
        return self.slope, self.intercept
    
    def predict(self, x):
        """使用線性回歸模型預測給定 x 值的 y 值"""
        if self.slope is None or self.intercept is None:
            self.calculate_regression()
        
        return self.slope * x + self.intercept
    
    def get_equation(self):
        """取得線性回歸方程式的字串表示"""
        if self.slope is None or self.intercept is None:
            self.calculate_regression()
        
        if self.intercept >= 0:
            return f"y = {self.slope:.4f}x + {self.intercept:.4f}"
        else:
            return f"y = {self.slope:.4f}x - {abs(self.intercept):.4f}"