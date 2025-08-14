from django.contrib import admin
from .models import (
    Problem,
    CrawlerSource,
    TestCase,
    Account,
    Task,
    CrawlTestCasesTask,
    CreateAccountsTask
)

# Register your models here.
admin.site.register(Problem)
admin.site.register(CrawlerSource)
admin.site.register(TestCase)
admin.site.register(Account)
admin.site.register(Task)
admin.site.register(CrawlTestCasesTask)
admin.site.register(CreateAccountsTask)