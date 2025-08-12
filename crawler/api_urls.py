from django.urls import path
from .views import CrawlTestCasesTaskView, TaskStatusView, CreateAccountsTaskView


urlpatterns = [
    # POST /api/tasks/crawl-testcases
    path('tasks/crawl-testcases', CrawlTestCasesTaskView.as_view(), name='api-task-crawl-testcases'),

    # GET /api/tasks/<uuid:task_id>
    path('tasks/<uuid:task_id>', TaskStatusView.as_view(), name='api-task-status'),

    # POST /api/tasks/create-accounts
    path('tasks/create-accounts', CreateAccountsTaskView.as_view(), name='api-task-create-accounts'),
]