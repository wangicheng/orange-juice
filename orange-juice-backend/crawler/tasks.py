import json
import logging
import time
from typing import List, Tuple, Dict
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Account, Task, TestCase, Problem, CrawlTestCasesTask, CreateAccountsTask, CrawlerSource
from .clients.oj_client import OJClient, Result
from .clients.exceptions import AccountExistsError, CaptchaError, OJClientError, OJServerError
from .core.crawler_core import CrawlerCore
from . import utils

logger = logging.getLogger(__name__)

class CrawlTestCasesSubmitter:
    def __init__(self, accounts: List[Tuple[Account, OJClient]], crawler_source: CrawlerSource, problem: Problem, header_code: str, footer_code: str):
        self.accounts = accounts
        self.problem = problem
        self.header_code = header_code
        self.footer_code = footer_code

        self.codes = crawler_source.code
        self.language = crawler_source.language
        self.problem_id = problem.oj_submit_id
        self._account_idx = 0
    
    def _add_header_and_footer_code(self, code: str) -> str:
        return f"{self.header_code}\n{code}\n{self.footer_code}"

    def _submit_and_get_memory_use(self, code: str):
        code = self._add_header_and_footer_code(code)
        acc, client = self.accounts[self._account_idx]
        self._account_idx = (self._account_idx + 1) % len(self.accounts)
        response = client.submit_code(code, self.language, self.problem_id)
        submission_id = response.get('data', {}).get('submission_id')
        acc.last_used = timezone.now()
        acc.save(update_fields=['last_used'])
        while True:
            time.sleep(0.5)
            submission = client.get_submission(submission_id)
            error = submission.get('error', None)
            if error:
                data = submission.get('data', None)
                raise OJServerError(f"Submission failed: {error} {data}")
            result = submission.get('data', {}).get('result')
            if result is None:
                raise OJClientError("Failed to get submission result.")
            if Result.is_judged(Result(result)):
                memory_use = submission.get('data', {}).get('statistic_info', {}).get('memory_cost')
                if memory_use is None:
                    raise OJClientError("Submission judged, but memory usage is missing.")
                return memory_use
        
    def found_testcase(self, testcase: str) -> None:
        TestCase.objects.get_or_create(problem=self.problem, content=testcase)

    def get_next_char(self, prefix: str, limit: int) -> int:
        return self._submit_and_get_memory_use(self.codes['get_next_char'].format(prefix=json.dumps(prefix), limit=limit))
    
    def get_prefix_length_length(self, prefix: str) -> int:
        return self._submit_and_get_memory_use(self.codes['get_prefix_length_length'].format(prefix=json.dumps(prefix)))

    def get_prefix_length(self, prefix: str, length_prefix: int, position: int) -> int:
        return self._submit_and_get_memory_use(self.codes['get_prefix_length'].format(prefix=json.dumps(prefix), length_prefix=length_prefix, position=position))

    def get_number(self, number: int) -> int:
        return self._submit_and_get_memory_use(self.codes['get_number'].format(number=number))

@shared_task(bind=True)
def crawl_test_cases_task(self, task_id):
    task = CrawlTestCasesTask.objects.get(id=task_id)
    
    # 用來存放本次任務確認可用的帳號
    # 格式可以是 (account_model, oj_client_instance)
    ready_account_pool: List[Tuple[Account, OJClient]] = []
    
    # 用來存放被鎖定的帳號模型，以便最後釋放
    locked_accounts = []

    try:
        task.status = Task.Status.IN_PROGRESS
        task.progress = 5 # 假設準備階段佔 5% 進度
        task.save()

        # --- 階段一：準備帳號池 ---
        num_accounts_needed = settings.ACCOUNTS_PER_CRAWL_TASK
        
        # 為了避免無限循環，我們設定一個查找上限
        max_candidates_to_check = num_accounts_needed * 3
        unused_accounts = []

        with transaction.atomic():
            # 撈出一批候選帳號並鎖定
            candidate_accounts = list(Account.objects.select_for_update().filter(
                status=Account.Status.ACTIVE
            )[:max_candidates_to_check])
            
            # 將它們全部標記為 IN_USE，避免其他任務干擾
            locked_account_ids = [acc.id for acc in candidate_accounts]
            Account.objects.filter(id__in=locked_account_ids).update(status=Account.Status.IN_USE)
            locked_accounts = candidate_accounts

        # 現在這些帳號被我們獨佔，可以安全地進行檢查
        for i, account in enumerate(locked_accounts):
            if len(ready_account_pool) + len(locked_accounts) - i < num_accounts_needed:
                # 預估帳號不夠
                break

            if len(ready_account_pool) >= num_accounts_needed:
                unused_accounts.append(account)
                continue # 帳號池已滿

            client = OJClient() # 創建一個 client 實例
            try:
                client.login(account.username, settings.DEFAULT_OJ_PASSWORD)
                ready_account_pool.append((account, client))
            except Exception as e:
                # 登入失敗可能是暫時性問題（如網路不穩），不應直接停用帳號。
                # 記錄此事件，並在任務結束時於 finally 區塊被釋放回 ACTIVE 狀態。
                unused_accounts.append(account)
                logger.warning(f"Account {account.username} login failed and will be skipped for this task. Error: {e}")
        
        if len(ready_account_pool) < num_accounts_needed:
            raise Exception(f"Failed to prepare enough usable accounts. Got {len(ready_account_pool)}, needed {num_accounts_needed}.")

        # --- 釋放所有未使用的帳號 ---
        if unused_accounts:
            unused_accounts_ids = [acc.id for acc in unused_accounts]
            Account.objects.filter(id__in=unused_accounts_ids).update(status=Account.Status.ACTIVE)

        # --- 階段二：執行核心任務 ---
        task.progress = 10
        task.save()
        
        # 在這裡，使用 ready_account_pool 中的帳號和 client 實例進行大量提交
        submitter = CrawlTestCasesSubmitter(ready_account_pool, task.crawler_source, task.problem, task.header_code, task.footer_code)
        crawler_core = CrawlerCore(submitter)
        crawler_core.run()
        
        task.status = Task.Status.SUCCESS
        task.progress = 100
        task.save()
        # ...

    except Exception as e:
        task.status = Task.Status.FAILURE
        task.result = {'error': str(e)}
        task.save()
    
    finally:
        # --- 釋放所有被鎖定的帳號 ---
        if locked_accounts:
            # 篩選出那些沒有被停用的帳號，將它們釋放回 ACTIVE
            active_again_ids = [
                acc.id for acc in locked_accounts 
                if acc.status != Account.Status.DISABLED
            ]
            if active_again_ids:
                Account.objects.filter(id__in=active_again_ids).update(status=Account.Status.ACTIVE)
        
@shared_task(bind=True)
def execute_create_accounts_task(self, task_id):
    """執行一個批量創建帳號的任務"""
    try:
        task = CreateAccountsTask.objects.get(id=task_id)
        task.status = Task.Status.IN_PROGRESS
        task.save(update_fields=['status'])
    except CreateAccountsTask.DoesNotExist:
        logging.warning("CreateAccountsTask DoesNotExist")
        return
        
    try:
        target_quantity = task.quantity
        success_count, failure_count = 0, 0
        max_failures = target_quantity * 2
        # ... (帳號創建的主迴圈) ...
        while success_count < target_quantity:
            if failure_count > max_failures:
                logging.error(f"Exceeded maximum failure limit ({max_failures}). Aborting task.")
                raise Exception(f"Exceeded maximum failure limit ({max_failures}). Aborting task.")
            
            new_username = utils.generate_random_username('orju', 28)
            try:
                client = OJClient()
                client.register(
                    username=new_username,
                    password=settings.DEFAULT_OJ_PASSWORD,
                    email=new_username + "@orange.juice.com"
                )
            except AccountExistsError:
                # 帳號已存在，不是致命錯誤，記錄日誌並繼續
                logging.info(f"Account {new_username} already exists, trying next.")
                failure_count += 1
                continue
            except CaptchaError:
                # 驗證碼錯誤，可以重試
                logging.warning("Captcha failed, retrying.")
                failure_count += 1
                continue
            else:
                # 成功後，儲存到資料庫
                Account.objects.create(username=new_username)
                success_count += 1
                # ... 更新進度 ...
                task.progress = success_count * 100 // target_quantity
                task.save(update_fields=['progress'])

        
        # 任務成功
        task.status = Task.Status.SUCCESS
        task.progress = 100
        task.result = {'message': f'Successfully created {target_quantity} accounts.'}
        task.save()

    except Exception as e:
        # 任務失敗
        logger.error(f"Task {task.id} failed unexpectedly.", exc_info=True)
        task.status = Task.Status.FAILURE
        task.result = {'error': str(e)}
        task.save()