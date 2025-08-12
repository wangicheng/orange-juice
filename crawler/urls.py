from django.urls import path
from .views import CreateAccountsControlPanelView, CrawlTestCasesControlPanelView


urlpatterns = [
    # GET /panel/tasks/create-accounts
    path('panel/tasks/create-accounts/', CreateAccountsControlPanelView.as_view(), name='panel-create-accounts'),
    # GET /panel/tasks/crawl-testcases
    path('panel/tasks/crawl-testcases/', CrawlTestCasesControlPanelView.as_view(), name='panel-crawl-testcases'),
]