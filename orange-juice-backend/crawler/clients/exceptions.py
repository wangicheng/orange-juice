class OJClientError(Exception):
    """所有 OJ Client 錯誤的基類"""
    pass

class CaptchaError(OJClientError):
    """驗證碼辨識或提交錯誤"""
    pass

class AccountExistsError(OJClientError):
    """註冊時帳號已存在"""
    pass

class OJServerError(OJClientError):
    """OJ 伺服器錯誤 (例如 500, 502)"""
    pass

class LoginFailedError(OJClientError):
    """登入失敗錯誤"""