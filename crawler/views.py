from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Problem, Task, CrawlerSource, CrawlTestCasesTask, CreateAccountsTask
from .tasks import crawl_test_cases_task, execute_create_accounts_task

# 新增這個 View 來顯示我們的控制面板頁面
class CreateAccountsControlPanelView(TemplateView):
    template_name = "crawler/create_accounts_panel.html"

# 新增爬取測資任務的控制面板 View
class CrawlTestCasesControlPanelView(TemplateView):
    template_name = "crawler/crawl_test_cases_panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['crawler_sources'] = CrawlerSource.objects.all()
        context['problems'] = Problem.objects.all()
        return context

class CrawlTestCasesTaskView(APIView):
    def post(self, request, *args, **kwargs):
        oj_problem_id = request.data.get('oj_problem_id')
        crawler_source_id = request.data.get('crawler_source_id')
        header_code = request.data.get('header_code', '')
        footer_code = request.data.get('footer_code', '')

        if not oj_problem_id:
            return Response(
                {"error": "oj_problem_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not crawler_source_id:
            return Response(
                {"error": "crawler_source_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        problem = Problem.objects.get(oj_display_id=oj_problem_id)
        crawler_source = CrawlerSource.objects.get(id=crawler_source_id)

        # 檢查 crawler_source 的 language 是否在 problem 的 allowed_languages 中
        if not problem.allowed_languages.count(crawler_source.language):
            return Response(
                {"error": f"Language '{crawler_source.language}' is not allowed for this problem."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 檢查是否有正在進行的任務
        existing_task = CrawlTestCasesTask.objects.filter(
            problem=problem,
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
        ).first()

        if existing_task:
            # 如果已有任務，直接返回該任務 ID
            return Response(
                {"task_id": existing_task.id},
                status=status.HTTP_202_ACCEPTED
            )

        # 建立新任務
        new_task = CrawlTestCasesTask.objects.create(
            problem=problem,
            crawler_source=crawler_source,
            header_code=header_code,
            footer_code=footer_code
        )

        # 推送任務到 Celery
        crawl_test_cases_task.delay(new_task.id)

        return Response(
            {"task_id": new_task.id},
            status=status.HTTP_202_ACCEPTED
        )

# 查詢任務狀態的 View (通常會放在另一個 class)
class TaskStatusView(APIView):
    def get(self, request, task_id, *args, **kwargs):
        try:
            task = Task.objects.get(id=task_id)
            # 這裡可以加上序列化器 (Serializer) 來回傳更完整的資訊
            response_data = {
                "id": task.id,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "updated_at": task.updated_at
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class CreateAccountsTaskView(APIView):
    """
    接收創建帳號的請求，並啟動一個非同步任務來執行。
    """
    def post(self, request, *args, **kwargs):
        """
        處理 POST /api/accounts/create 請求。
        """
        # 1. 從請求中獲取數量
        try:
            quantity = int(request.data.get('quantity'))
            if quantity <= 0:
                raise ValueError("Quantity must be a positive integer.")
        except (ValueError, TypeError):
            return Response(
                {"error": "A valid positive 'quantity' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 創建一個 CreateAccountsTask 實例
        # 因為 CreateAccountsTask 繼承自 Task，Django 會自動在兩個表中都創建記錄
        # Task 模型中的共通欄位 (status, progress 等) 會自動設定預設值
        new_task = CreateAccountsTask.objects.create(
            quantity=quantity
        )

        # 3. 將任務推送到 Celery
        # 我們傳遞 task 的 id，讓 Celery worker 能夠從資料庫中找到它
        execute_create_accounts_task.delay(new_task.id)

        # 4. 返回任務 ID，讓前端可以追蹤進度
        return Response(
            {"task_id": new_task.id},
            status=status.HTTP_202_ACCEPTED
        )