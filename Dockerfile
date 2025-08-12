# 使用官方的 Python 映像檔作為基礎
FROM python:3.12-slim

# 設定環境變數，防止 Python 寫入 .pyc 檔案
ENV PYTHONDONTWRITEBYTECODE 1
# 讓 Python 輸出立即顯示在終端，方便除錯
ENV PYTHONUNBUFFERED 1

# 設定工作目錄
WORKDIR /app

# 複製依賴套件列表並安裝
# 這樣做可以利用 Docker 的快取機制，如果 requirements.txt 沒變，就不會重新安裝
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案的其餘程式碼
COPY . /app/

# Port 8000 將會被 Django 開發伺服器使用
EXPOSE 8000