from typing import Protocol, runtime_checkable, List, Optional
from dataclasses import dataclass, field

from .linear_regression import LinearRegression

@dataclass
class CrawlerState:
    """保存 CrawlerCore 的執行狀態，以便中斷後可以恢復。"""
    state: str = "NEEDS_PREDICT"
    prefix: str = ""
    limit: int = 256
    prefix_length_length: int = 0
    prefix_length: int = 0
    position: int = 0
    # 保存 LinearRegression 的狀態
    lr_slope: Optional[float] = None
    lr_intercept: Optional[float] = None

@runtime_checkable
class Submitter(Protocol):
    """
    定義了一個「程式碼提交者」的行為介面。
    任何實現了這個介面的類，都可以被 CrawlerCore 使用。
    """

    def found_testcase(self, testcase: str) -> None:
        ...
    
    def get_next_char(self, prefix: str, limit: int) -> int:
        ...
    
    def get_prefix_length_length(self, prefix: str) -> int:
        ...

    def get_prefix_length(self, prefix: str, length_prefix: int, position: int) -> int:
        ...

    def get_number(self, number: int) -> int:
        ...

class CrawlerCore:
    def __init__(self, submitter: Submitter, should_pause: callable = lambda: False):
        self.submitter = submitter
        self.linear_regression: Optional[LinearRegression] = None
        self.should_pause = should_pause
        # 初始化內部狀態
        self._set_initial_state()

    def _set_initial_state(self):
        """將內部狀態重設為初始值。"""
        self.current_internal_state = "NEEDS_PREDICT"
        self.prefix = ""
        self.limit = 256
        self.prefix_length_length = 0
        self.prefix_length = 0
        self.position = 0
        self.linear_regression = None

    def load_state(self, state: CrawlerState):
        """從 state 物件載入執行狀態。"""
        self.current_internal_state = state.state
        self.prefix = state.prefix
        self.limit = state.limit
        self.prefix_length_length = state.prefix_length_length
        self.prefix_length = state.prefix_length
        self.position = state.position
        if state.lr_slope is not None and state.lr_intercept is not None:
            self.linear_regression = LinearRegression()
            self.linear_regression.slope = state.lr_slope
            self.linear_regression.intercept = state.lr_intercept
        else:
            self.linear_regression = None

    def save_state(self) -> CrawlerState:
        """將當前執行狀態儲存到 state 物件。"""
        lr_slope, lr_intercept = None, None
        if self.linear_regression and self.linear_regression.slope is not None:
            lr_slope = self.linear_regression.slope
            lr_intercept = self.linear_regression.intercept

        return CrawlerState(
            state=self.current_internal_state,
            prefix=self.prefix,
            limit=self.limit,
            prefix_length_length=self.prefix_length_length,
            prefix_length=self.prefix_length,
            position=self.position,
            lr_slope=lr_slope,
            lr_intercept=lr_intercept
        )
    
    def run(self):
        """
        執行爬蟲主循環。
        如果發生錯誤，會拋出異常，呼叫者應捕捉異常並使用 save_state() 保存狀態。
        """
        try:
            if self.current_internal_state == "NEEDS_PREDICT":
                self._run_predict()
                self.prefix = ""
                self.limit = 256
                self.current_internal_state = "FINDING_NEXT_CHAR"

            while self.current_internal_state != "DONE":
                if self.should_pause():
                    return

                if self.current_internal_state == "FINDING_NEXT_CHAR":
                    while True:
                        if self.should_pause():
                            return
                        char = self._m2n(self.submitter.get_next_char(self.prefix, self.limit))
                        if char == 0:
                            self.submitter.found_testcase(self.prefix)
                            self.current_internal_state = "FINDING_PREFIX_LENGTH_LENGTH"
                            break
                        self.prefix += chr(char)
                        self.limit = 256
                
                elif self.current_internal_state == "FINDING_PREFIX_LENGTH_LENGTH":
                    self.prefix_length_length = self._m2n(self.submitter.get_prefix_length_length(self.prefix))
                    if self.prefix_length_length == -1:
                        self.current_internal_state = "DONE"
                        continue
                    self.prefix_length = 0
                    self.position = self.prefix_length_length - 1
                    self.current_internal_state = "FINDING_PREFIX_LENGTH"

                elif self.current_internal_state == "FINDING_PREFIX_LENGTH":
                    while self.position >= 0:
                        number = self._m2n(self.submitter.get_prefix_length(self.prefix, self.prefix_length, self.position))
                        self.prefix_length = self.prefix_length * 256 + number
                        self.position -= 1
                    
                    self.limit = ord(self.prefix[self.prefix_length])
                    self.prefix = self.prefix[:self.prefix_length]
                    self.current_internal_state = "FINDING_NEXT_CHAR"

        except Exception as e:
            print(f"在狀態 '{self.current_internal_state}' 發生錯誤: {e}")
            print("執行已暫停。請保存狀態以便稍後恢復。")
            raise
    
    def _run_predict(self):
        self.linear_regression = LinearRegression()
        for number in range(-1, 256, 64):
            memory_use = self.submitter.get_number(number)
            self.linear_regression.add_point(memory_use, number)
        self.linear_regression.calculate_regression()
    
    def _m2n(self, memory_use: int) -> int:
        if not self.linear_regression:
            raise RuntimeError("LinearRegression model not predicted yet.")
        return round(self.linear_regression.predict(memory_use))
