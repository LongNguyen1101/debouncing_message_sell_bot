import json
from typing import Any
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from app.redis_client import r
from requests_sse import EventSource
from dotenv import load_dotenv
import os
from requests import RequestException
import requests
import uuid

load_dotenv(override=True)

CHATBOT_URL = os.getenv("CHATBOT_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL_PRODUCTION")
# WEBHOOK_URL = os.getenv("WEBHOOK_URL_TEST")
mapper_uuid = {}

def send_messages_to_n8n(chat_id: str, content: str) -> str:
    status = ""
    payload = {
        "chat_id": chat_id,
        "content": content
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        
        status = "OK"
    except requests.RequestException as e:
        status = f"[ERROR] Failed sending to n8n: {e}"
    finally:
        return status

def send_messages_to_chatbot(chat_id: str, content: str, get_uuid: str) -> Any:
    print(f">>>> sending messages: {content}")
    payload = {"chat_id": chat_id, "user_input": content, "uuid": get_uuid}
    headers = {"Accept": "text/event-stream"}
    
    try:
        with EventSource(
            CHATBOT_URL,
            method="POST",
            headers=headers,
            json=payload,
            timeout=100
        ) as source:
            for event in source:
                print(">>>> SSE event:", event.data if hasattr(event, 'data') else event)
                if hasattr(event, 'data'):
                    if event.data == "[DONE]":
                        print(">>>> Close SSE connection")
                        source.close()
                        break
                    else:
                        status = send_messages_to_n8n(chat_id=chat_id, content=event.data)
                        print(f">>>> Status send to n8n: {status}")
                    
    except RequestException as e:
        print(f"[ERROR] gửi SSE thất bại: {e}")
    finally:
        if source:
            source.close()
            
def start_restart_chatbot(chat_id: str) -> Any:
    try:
        response = (
            "Chào khách, em rất vui được hỗ trợ khách. Nếu khách có thắc mắc hoặc "
            "cần tư vấn về các sản phẩm điện tử thông minh của cửa hàng, hãy cho em biết nhé! Em rất sẵn lòng giúp đỡ.\n"
            "(đã reset hoặc tạo mới đoạn chat).\n"
        )
        content = json.dumps({"content": response})
        status = send_messages_to_n8n(chat_id=chat_id, content=content)
        print(f">>>> Status send to n8n: {status}")
                    
    except RequestException as e:
        print(f"[ERROR] gửi SSE thất bại: {e}")

# def process_messages(chat_id: str):
#     key_list = f"messages:{chat_id}"
#     msgs = r.lrange(key_list, 0, -1)
    
#     if not msgs:
#         return
#     each = [m for m in msgs]
#     content = ", ".join(s for s in each).strip()
#     r.delete(key_list)
    
#     get_uuid = mapper_uuid.get(chat_id)
#     if not get_uuid:
#         get_uuid = str(uuid.uuid4())
#         mapper_uuid[chat_id] = get_uuid
        
#     print(f">>>> Process for {chat_id}: {content} | uuid: {get_uuid}")
    
#     if content == "/restart" or content == "/start":
#         print(f">>>> Old uuid: {get_uuid}")
#         get_uuid = str(uuid.uuid4())
#         mapper_uuid[chat_id] = get_uuid
#         print(f">>>> New uuid: {get_uuid}")
        
#         start_restart_chatbot(chat_id)
#     else:
#         send_messages_to_chatbot(chat_id, content, get_uuid)
    
# Lua script release lock an toàn
RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
"""
release_lock = r.register_script(RELEASE_SCRIPT)

def acquire_lock(lock_key: str, ttl_ms: int = 6000) -> str | None:
    token = str(uuid.uuid4())
    ok = r.set(lock_key, token, nx=True, px=ttl_ms)
    return token if ok else None

def free_lock(lock_key: str, token: str) -> None:
    try:
        release_lock(keys=[lock_key], args=[token])
    except Exception as e:
        print(f"[WARN] free_lock exception: {e}")

def process_messages(chat_id: str):
    lock_key = f"debounce_lock:{chat_id}"
    token = acquire_lock(lock_key)
    if not token:
        print(f">>>> Skip process_messages({chat_id}): already locked")
        return

    try:
        key_list = f"messages:{chat_id}"
        msgs = r.lrange(key_list, 0, -1)
        if not msgs:
            return
        content = ", ".join(m for m in msgs).strip()
        r.delete(key_list)

        get_uuid = mapper_uuid.get(chat_id)
        if not get_uuid:
            get_uuid = str(uuid.uuid4())
            mapper_uuid[chat_id] = get_uuid

        print(f">>>> Process for {chat_id}: {content} | uuid: {get_uuid}")
        print(f">>>> Mapper uuid: {mapper_uuid}")

        if content in ("/restart", "/start"):
            get_uuid = str(uuid.uuid4())
            mapper_uuid[chat_id] = get_uuid
            print(f">>>> New uuid: {get_uuid}")
            start_restart_chatbot(chat_id)
        else:
            send_messages_to_chatbot(chat_id, content, get_uuid)

    finally:
        free_lock(lock_key, token)