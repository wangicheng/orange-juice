from django.urls import path
from .views import (
    GetCSRFToken,
    CrawlTestCasesTaskView,
    CreateAccountsTaskView,
    TaskStatusView,
    ProblemListView,
    CrawlerSourceListView,
    ProblemDetailView,
    TestCaseListView,
    ResumeCrawlTaskView,
)


urlpatterns = [
    path('csrf-cookie/', GetCSRFToken.as_view(), name='get-csrf-token'), # 以後可以移至專門的 APP 中
    
    path('tasks/crawl-testcases/', CrawlTestCasesTaskView.as_view(), name='create_crawl_task'),
    path('tasks/<uuid:task_id>/status/', TaskStatusView.as_view(), name='task_status'),
    path('tasks/<uuid:task_id>/resume/', ResumeCrawlTaskView.as_view(), name='resume_crawl_task'),
    path('tasks/create-accounts/', CreateAccountsTaskView.as_view(), name='create_accounts_task'),

    path('problems/', ProblemListView.as_view(), name='problem-list'),
    path('problems/<str:problem_id>/', ProblemDetailView.as_view(), name='problem-detail'),
    path('problems/<str:problem_id>/testcases/', TestCaseListView.as_view(), name='testcase-list'),
    path('crawler-sources/', CrawlerSourceListView.as_view(), name='crawler-source-list'),
]