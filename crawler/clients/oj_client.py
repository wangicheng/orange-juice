import base64
from enum import IntEnum
from io import BytesIO

import requests
from django.conf import settings
from urllib.parse import urljoin

from .captcha_solver import solve_captcha
from .exceptions import OJClientError, CaptchaError, AccountExistsError, OJServerError, LoginFailedError

import logging

logger = logging.getLogger(__name__)


class Result(IntEnum):
    """
    定義 OJ 判題結果的枚舉。
    繼承自 IntEnum，使其成員可以直接當作整數比較。
    """
    # 1. 直接定義所有標準的枚舉成員
    NONE = -10
    CE = -2
    WA = -1
    AC = 0
    TLE = 1
    MLE = 3
    RE = 4
    SE = 5
    PENDING = 6
    JUDGING = 7
    PAC = 8

    # 2. 建立一個工廠方法，專門用來處理來自 API 的、可能需要轉換的值
    @classmethod
    def from_api_value(cls, api_value: int):
        """
        從 API 回傳的原始值創建 Result 枚舉。
        這個方法會處理非標準的別名值。
        """
        # 建立一個別名 -> 枚舉成員 的映射字典
        # 這樣更直接，也更清晰
        alias_map = {
            -3: cls.MLE,   # API 回傳 -3 時，我們將它視為 Result.MLE
            2:  cls.TLE,   # API 回傳 2 時，我們將它視為 Result.TLE
        }

        # 優先從別名映射中尋找
        if api_value in alias_map:
            return alias_map[api_value]
        
        # 如果不是別名，就嘗試用標準方式從值創建枚舉
        # IntEnum(value) 如果找不到對應值會自動拋出 ValueError
        try:
            return cls(api_value)
        except ValueError:
            # 捕獲標準的 ValueError 並拋出我們自訂的、資訊更豐富的錯誤
            raise ValueError(f"'{api_value}' is not a valid or aliased value for {cls.__name__}")

    # 3. 你的輔助方法可以保持不變
    @classmethod
    def is_judged(cls, status) -> bool:
        """一個好用的輔助方法，判斷是否已出結果"""
        return status not in (cls.PENDING, cls.JUDGING)

class OJClient:
    """
    與 Online Judge 平台互動的客戶端。
    負責處理 HTTP 請求、Session 管理和錯誤處理。
    """
    def __init__(self):
        """
        初始化 OJClient。
        """
        self.session = requests.Session()
        self.base_url = settings.OJ_BASE_URL 
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
        })
        
        self._csrf_token = None

    def _get_url(self, endpoint: str) -> str:
        """輔助函數，產生完整的請求 URL"""
        return urljoin(self.base_url, endpoint)

    def _get_and_update_csrf_token(self):
        """
        訪問一個無害的頁面來獲取 CSRF Token，並設定到請求標頭。
        這是許多需要 Token 的操作的第一步。
        """
        try:
            # 訪問一個通常會設定 cookie 的頁面，例如 /about 或 /api/profile
            self.session.get(self._get_url("/api/profile"), timeout=10) 
            if 'csrftoken' in self.session.cookies:
                self._csrf_token = self.session.cookies['csrftoken']
                self.session.headers['X-CSRFToken'] = self._csrf_token
            else:
                # 如果第一次沒有，有些網站會在 POST 前的 GET 請求中提供
                # 這裡可以根據實際情況決定是否拋出錯誤或再次嘗試
                raise OJClientError("Failed to get initial csrftoken.")
        except requests.exceptions.RequestException as e:
            raise OJServerError(f"Network error while fetching CSRF token: {e}")

    def register(self, username: str, password: str, email: str) -> None:
        """
        執行註冊流程，**不包含登入**。

        Args:
            username (str): 要註冊的用戶名。
            password (str): 要註冊的密碼。
            email (str): 要註冊的電子郵件。

        Raises:
            CaptchaError, AccountExistsError, OJServerError, OJClientError
        """
        try:
            # --- 步驟 1: 確保我們有 CSRF Token ---
            self._get_and_update_csrf_token()

            # --- 步驟 2: 獲取驗證碼 ---
            response = self.session.get(self._get_url("/api/captcha"), timeout=10)
            response.raise_for_status()
            captcha_data = response.json()
            
            base64_str = captcha_data.get('data', '').split(',')[-1]
            if not base64_str:
                raise OJClientError("Captcha data is empty in the response.")

            # --- 步驟 3: 辨識驗證碼 ---
            captcha_image_bytes = base64.b64decode(base64_str)
            captcha_solution = solve_captcha(BytesIO(captcha_image_bytes))

            # --- 步驟 4: 提交註冊請求 ---
            register_payload = {
                "username": username,
                "password": password,
                "email": email,
                "captcha": captcha_solution,
            }
            reg_response = self.session.post(
                self._get_url("/api/register"),
                json=register_payload,
                timeout=15
            )
            reg_response.raise_for_status()
            
            reg_data = reg_response.json()
            
            # 根據 OJ API 的實際回應來判斷錯誤類型
            # 假設 'error' 欄位存在表示有錯誤
            if reg_data.get("error"):
                error_msg = reg_data.get("data")
                if "Username already exists" in error_msg:
                    raise AccountExistsError(f"Account '{username}' already exists.")
                if "Invalid captcha" in error_msg:
                    raise CaptchaError("Captcha solution was incorrect.")
                raise OJClientError(f"Registration failed: {error_msg}")

            # 註冊成功，不需要做任何事，方法結束
            # self.session 中沒有 sessionid

        except requests.exceptions.RequestException as e:
            raise OJServerError(f"Network error during registration: {e}")
        except (KeyError, ValueError, TypeError) as e:
            raise OJClientError(f"Failed to parse response or data during registration: {e}")

    def login(self, username: str, password: str) -> None:
        """
        使用已有的帳號密碼登入。
        成功後，sessionid 和 csrftoken 會被保存在 self.session 中。

        Args:
            username (str): 登入的用戶名。
            password (str): 登入的密碼。
        
        Raises:
            LoginFailedError: 如果用戶名或密碼錯誤。
            OJServerError, OJClientError
        """
        try:
            # --- 步驟 1: 確保我們有 CSRF Token ---
            # 登入操作通常也需要 CSRF 保護
            self._get_and_update_csrf_token()

            # --- 步驟 2: 執行登入 ---
            login_payload = {
                "username": username,
                "password": password
            }
            login_response = self.session.post(
                self._get_url("/api/login"),
                json=login_payload,
                timeout=15
            )
            login_response.raise_for_status()

            login_data = login_response.json()
            
            # 判斷登入是否成功
            if login_data.get("error"):
                error_msg = login_data.get("data", "Unknown login error")
                # 假設用戶名密碼錯誤會返回特定訊息
                if "User does not exist or password is not correct" in error_msg:
                    raise LoginFailedError(error_msg)
                raise OJClientError(f"Login failed: {error_msg}")

            # --- 步驟 3: 驗證登入狀態 ---
            # 檢查 sessionid 是否已成功設定在 cookies 中
            if 'sessionid' not in self.session.cookies:
                raise OJClientError("Login appears successful, but sessionid not found in cookies.")
            
            # 更新 CSRF Token，因為登入後可能會刷新
            if 'csrftoken' in self.session.cookies:
                 self._csrf_token = self.session.cookies['csrftoken']
                 self.session.headers['X-CSRFToken'] = self._csrf_token

        except requests.exceptions.RequestException as e:
            raise OJServerError(f"Network error during login: {e}")
        except (KeyError, ValueError, TypeError) as e:
            raise OJClientError(f"Failed to parse response or data during login: {e}")
    
    def submit_code(self, code: str, language: str, problem_id: int):
        payload = {
            "code": code,
            "language": language,
            "problem_id": int(problem_id)
        }
        response = self.session.post(
            self._get_url("/api/submission"),
            data=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    
    def get_submission(self, submission_id: str):
        params = {
            "id": submission_id
        }
        response = self.session.get(
            self._get_url("/api/submission"),
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
