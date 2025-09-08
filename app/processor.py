import os
import uuid
import requests
from typing import Any
from dotenv import load_dotenv

from requests_sse import EventSource
from requests import RequestException

from app.redis_client import r

from app.log.logger_config import setup_logging

logger = setup_logging(__name__)

load_dotenv(override=True)

CHATBOT_URL = os.getenv("CHATBOT_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL_PRODUCTION")
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
        logger.error(f"Lỗi gửi tin nhắn tới n8n: {e}")
        status = f"[ERROR] Failed sending to n8n: {e}"
    finally:
        return status

def send_messages_to_chatbot(chat_id: str, content: str) -> Any:
    logger.info(f"Sending messages: {content}")
    payload = {"chat_id": chat_id, "user_input": content}
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
                logger.info(f"SSE event: {event.data if hasattr(event, 'data') else event}")
                if hasattr(event, 'data'):
                    if event.data == "[DONE]":
                        logger.info("Close SSE connection")
                        source.close()
                        break
                    else:
                        status = send_messages_to_n8n(chat_id=chat_id, content=event.data)
                        logger.info(f"Status send to n8n: {status}")
                    
    except RequestException as e:
        logger.error(f"[ERROR] gửi SSE thất bại: {e}")
    finally:
        if source:
            source.close()

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
        logger.error(f"[WARN] free_lock exception: {e}")

def process_messages(chat_id: str):
    lock_key = f"debounce_lock:{chat_id}"
    token = acquire_lock(lock_key)
    if not token:
        logger.info(f"Skip process_messages({chat_id}): already locked")
        return

    try:
        key_list = f"messages:{chat_id}"
        msgs = r.lrange(key_list, 0, -1)
        if not msgs:
            return
        content = ", ".join(m for m in msgs).strip()
        r.delete(key_list)

        send_messages_to_chatbot(chat_id, content)

    finally:
        free_lock(lock_key, token)