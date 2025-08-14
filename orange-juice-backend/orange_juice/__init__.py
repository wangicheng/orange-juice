# 這會確保 app 在 Django 啟動時被載入，
# 這樣 @shared_task 裝飾器才能正常運作。
from .celery import app as celery_app

__all__ = ('celery_app',)