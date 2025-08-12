import os
from celery import Celery

# 設定 Django 的 settings 模組
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orange_juice.settings')

app = Celery('orange_juice')

# 使用 Django settings 來設定 Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動從所有註冊的 Django app 中尋找 tasks.py
app.autodiscover_tasks()