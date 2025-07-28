from typing import Any
from app.redis_client import r
from requests_sse import EventSource
from dotenv import load_dotenv
import os
from requests import RequestException
import requests

load_dotenv(override=True)

CHATBOT_URL = os.getenv("CHATBOT_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL_PRODUCTION")

def send_messages_to_n8n(chat_id: str, content: str) -> Any:
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
        
        return "OK"
    except requests.RequestException as e:
        return f"[ERROR] Failed sending to n8n: {e}"

def send_messages_to_chatbot(chat_id: str, content: str) -> Any:
    print(f">>>> sending messages: {content}")
    payload = {"chat_id": chat_id, "user_input": content}
    headers = {"Accept": "text/event-stream"}
    try:
        with EventSource(
            CHATBOT_URL,
            method="POST",
            headers=headers,
            json=payload,
            timeout=30
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
                        print(f"Status send to n8n: {status}")
                    
    except RequestException as e:
        print(f"[ERROR] gửi SSE thất bại: {e}")
    finally:
        if source:
            source.close()

def process_messages(chat_id: str):
    key_list = f"messages:{chat_id}"
    msgs = r.lrange(key_list, 0, -1)
    if not msgs:
        return
    each = [m for m in msgs]
    print(f">>>> Process for {chat_id}: {each}")
    
    content = ". ".join(s for s in each).strip()
    r.delete(key_list)
    
    send_messages_to_chatbot(chat_id, content)
    