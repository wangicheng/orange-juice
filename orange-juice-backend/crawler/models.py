# your_app/models.py
import uuid
from django.db import models

class Problem(models.Model):
    oj_display_id = models.CharField(max_length=50, unique=True, db_index=True, help_text="會在 URL 中使用的 ID，例如 PR113-2-12")
    oj_submit_id = models.IntegerField(unique=True, help_text="發送繳交請求時會用到的 ID，例如 1231")
    title = models.CharField(max_length=255)
    allowed_languages = models.JSONField(default=list, help_text="例如 ['C++', 'Python', 'Java']")

    def __str__(self):
        return f"{self.oj_display_id}: {self.title}"

class CrawlerSource(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="給這個爬蟲程式一個好記的名字，例如 'C++ Memory Eater v1'")
    language = models.CharField(max_length=50, help_text="這個程式碼的語言，例如 'C++'")
    code = models.JSONField(help_text="完整的爬蟲原始碼，以 JSON 格式儲存")
    description = models.TextField(blank=True, help_text="描述這個版本的特點或適用場景")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='test_cases')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Account(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE'
        IN_USE = 'IN_USE'
        DISABLED = 'DISABLED'

    username = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

# 1. Task 是父模型，包含所有共通欄位。它不是抽象的。
class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        IN_PROGRESS = 'IN_PROGRESS'
        SUCCESS = 'SUCCESS'
        FAILURE = 'FAILURE'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress = models.IntegerField(default=0)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task {self.id} ({self.status})"


# 2. 具體的任務模型，直接繼承自 Task
class CrawlTestCasesTask(Task):
    # CrawlTask 專屬的欄位
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    crawler_source = models.ForeignKey(CrawlerSource, on_delete=models.PROTECT)
    header_code = models.TextField(blank=True)
    footer_code = models.TextField(blank=True)

    def __str__(self):
        return f"Crawl Task for {self.problem.oj_display_id}"


class CreateAccountsTask(Task):
    # CreateAccountsTask 專屬的欄位
    quantity = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Create {self.quantity} Accounts Task"