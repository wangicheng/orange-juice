from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Problem, Task, CrawlerSource, CrawlTestCasesTask, CreateAccountsTask, TestCase
from .tasks import crawl_test_cases_task, execute_create_accounts_task
from .serializers import ProblemSerializer, CrawlerSourceSerializer, TestCaseSerializer

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': 'CSRF cookie set'})

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
            
            response_data = {
                "id": task.id,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "updated_at": task.updated_at
            }

            # 嘗試獲取具體的任務子類，以便訪問其專有欄位
            try:
                crawl_task = task.crawltestcasestask
                response_data['task_type'] = 'CrawlTestCasesTask'
                response_data['crawler_state'] = crawl_task.crawler_state
            except CrawlTestCasesTask.DoesNotExist:
                try:
                    # 如果需要，也可以處理其他任務類型
                    task.createaccountstask
                    response_data['task_type'] = 'CreateAccountsTask'
                except CreateAccountsTask.DoesNotExist:
                    response_data['task_type'] = 'Task'

            return Response(response_data, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class ResumeCrawlTaskView(APIView):
    def post(self, request, task_id, *args, **kwargs):
        try:
            task = CrawlTestCasesTask.objects.get(id=task_id)
        except CrawlTestCasesTask.DoesNotExist:
            return Response({"error": "Crawl task not found."}, status=status.HTTP_404_NOT_FOUND)

        # 只允許從 FAILURE 狀態恢復
        if task.status != Task.Status.FAILURE:
            return Response(
                {"error": f"Task is in '{task.status}' state and cannot be resumed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 如果請求中有提供新的 state，就更新它
        new_state = request.data.get('crawler_state')
        if new_state is not None:
            task.crawler_state = new_state
        
        # 重設任務狀態以便重新執行
        task.status = Task.Status.PENDING
        task.progress = 0
        task.result = {"message": "Task has been resumed by user."}
        task.save()

        # 重新將任務推送到 Celery
        crawl_test_cases_task.delay(task.id)

        return Response(
            {"message": "Task has been successfully queued for resumption.", "task_id": task.id},
            status=status.HTTP_200_OK
        )

class CreateAccountsTaskView(APIView):
    """
    接收創建帳號的請求，並啟動一個非同步任務來執行。
    """
    def post(self, request, *args, **kwargs):
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

class PauseTaskView(APIView):
    def post(self, request, task_id, *args, **kwargs):
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        if task.status not in [Task.Status.PENDING, Task.Status.IN_PROGRESS]:
            return Response(
                {"error": f"Task is in '{task.status}' state and cannot be paused."},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.status = Task.Status.PAUSED
        task.result = {"message": "Task pause request received."}
        task.save()

        return Response(
            {"message": "Task has been marked for pausing.", "task_id": task.id},
            status=status.HTTP_200_OK
        )

class ResumeCrawlTaskView(APIView):
    def post(self, request, task_id, *args, **kwargs):
        try:
            task = CrawlTestCasesTask.objects.get(id=task_id)
        except CrawlTestCasesTask.DoesNotExist:
            return Response({"error": "Crawl task not found."}, status=status.HTTP_404_NOT_FOUND)

        # 只允許從 FAILURE 或 PAUSED 狀態恢復
        if task.status not in [Task.Status.FAILURE, Task.Status.PAUSED]:
            return Response(
                {"error": f"Task is in '{task.status}' state and cannot be resumed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 如果請求中有提供新的 state，就更新它
        new_state = request.data.get('crawler_state')
        if new_state is not None:
            task.crawler_state = new_state
        
        # 重設任務狀態以便重新執行
        task.status = Task.Status.PENDING
        task.progress = 0
        task.result = {"message": "Task has been resumed by user."}
        task.save()

        # 重新將任務推送到 Celery
        crawl_test_cases_task.delay(task.id)

        return Response(
            {"message": "Task has been successfully queued for resumption.", "task_id": task.id},
            status=status.HTTP_200_OK
        )

# Add these new API List Views
class ProblemListView(generics.ListAPIView):
    queryset = Problem.objects.all().order_by('oj_display_id')
    serializer_class = ProblemSerializer

class CrawlerSourceListView(generics.ListAPIView):
    queryset = CrawlerSource.objects.all().order_by('name')
    serializer_class = CrawlerSourceSerializer

class ProblemDetailView(generics.RetrieveAPIView):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer
    lookup_field = 'oj_display_id'
    lookup_url_kwarg = 'problem_id'

class TestCaseListView(generics.ListAPIView):
    serializer_class = TestCaseSerializer

    def get_queryset(self):
        problem_id = self.kwargs['problem_id']
        return TestCase.objects.filter(problem__oj_display_id=problem_id).order_by('created_at')