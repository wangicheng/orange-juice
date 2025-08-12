from typing import Protocol, runtime_checkable

from .linear_regression import LinearRegression

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
    def __init__(self, submitter: Submitter):
        self.submitter = submitter
        self.linear_regression: LinearRegression = None
        self.prefix = ""
        self.testcases = []
    
    def run(self):
        self._run_predict()
        self.prefix = ""
        self.testcases = []
        limit = 256
        while True:
            while True:
                char = self._m2n(self.submitter.get_next_char(self.prefix, limit))
                if char == 0:
                    self.submitter.found_testcase(self.prefix)
                    self.testcases.append(self.prefix)
                    break
                self.prefix += chr(char)
                limit = 256
            prefix_length_length = self._m2n(self.submitter.get_prefix_length_length(self.prefix))
            if prefix_length_length == -1:
                break
            prefix_length = 0
            for position in range(prefix_length_length - 1, -1, -1):
                number = self._m2n(self.submitter.get_prefix_length(self.prefix, prefix_length, position))
                prefix_length = prefix_length * 256 + number
            limit = ord(self.prefix[prefix_length])
            self.prefix = self.prefix[:prefix_length]
        return self.testcases
    
    def _run_predict(self):
        self.linear_regression = LinearRegression()
        for number in range(-1, 256, 64):
            memory_use = self.submitter.get_number(number)
            self.linear_regression.add_point(memory_use, number)
        self.linear_regression.calculate_regression()
    
    def _m2n(self, memory_use: int) -> int:
        return round(self.linear_regression.predict(memory_use))


    