import json
from app.redis_client import r

def push_message(chat_id: str, content: str, debounce_ms: int = 5000):
    list_key = f"messages:{chat_id}"
    debounce_key = f"debounce:{chat_id}"
    r.rpush(list_key, content)
    # NX: tạo mới nếu không có, XX: set lại TTL nếu đã tồn tại
    if r.set(debounce_key, "", nx=True, px=debounce_ms):
        pass
    else:
        r.set(debounce_key, "", xx=True, px=debounce_ms)
