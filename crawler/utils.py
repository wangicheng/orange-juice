import random
import string

def generate_random_username(prefix="test_acct_", length=8):
    """產生一個帶有前綴的隨機用戶名"""
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{random_part}"