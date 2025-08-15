from django.urls import path
from .views import PauseTaskView, ResumeCrawlTaskView

urlpatterns = [
    path('api/tasks/<uuid:task_id>/pause/', PauseTaskView.as_view(), name='task-pause'),
    path('api/tasks/<uuid:task_id>/resume/', ResumeCrawlTaskView.as_view(), name='resume-crawl-task'),
]