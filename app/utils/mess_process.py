import redis
import threading
import time
import json
import os

r = redis.Redis(host='localhost', port=6379, db=0)

# --- TẮT LƯU DB ---
r.config_set("save", "")
r.config_set("appendonly", "no")
if os.path.exists("dump.rdb"):
    os.remove("dump.rdb")

# Đăng ký listener key-expire events
pubsub = r.pubsub()
pubsub.psubscribe('__keyevent@0__:expired')

def process_messages(user_id):
    key_list = f"messages:{user_id}"
    msgs = r.lrange(key_list, 0, -1)
    if not msgs:
        return
    each = [m.decode('utf-8') for m in reversed(msgs)]
    print(f">> Process for {user_id}: {each}")
    r.delete(key_list)

def pubsub_listener():
    for m in pubsub.listen():
        if m['type'] == 'pmessage':
            exp_key = m['data'].decode('utf-8')
            if exp_key.startswith("debounce:"):
                user_id = exp_key.split(":",1)[1]
                process_messages(user_id)

threading.Thread(target=pubsub_listener, daemon=True).start()

def on_new_message(user_id, msg):
    list_key = f"messages:{user_id}"
    debounce_key = f"debounce:{user_id}"
    r.rpush(list_key, json.dumps(msg))
    if r.set(debounce_key, "", nx=True, px=5000):
        pass
    else:
        r.set(debounce_key, "", xx=True, px=5000)

# Ví dụ mô phỏng
if __name__ == "__main__":
    my = "user123"
    on_new_message(my, {"text":"Hello"})
    time.sleep(2)
    on_new_message(my, {"text":"Again"})
    time.sleep(6)
