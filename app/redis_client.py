import os
import redis
from threading import Thread
import os

REDIS_URL = os.getenv("REDIS_URL")

# r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0, decode_responses=False)
r = redis.from_url(REDIS_URL)

# disable persistence
# For testing only
r.config_set("save", "")
r.config_set("appendonly", "no")
if os.path.exists("dump.rdb"):
    os.remove("dump.rdb")

# enable key expiration events
r.config_set("notify-keyspace-events", "Ex")

def listener():
    pubsub = r.pubsub()
    pubsub.psubscribe('__keyevent@0__:expired')
    for m in pubsub.listen():
        if m['type'] == 'pmessage':
            exp_key = m['data'].decode()
            if exp_key.startswith("debounce:"):
                chat_id = exp_key.split(":", 1)[1]
                
                from app.processor import process_messages
                process_messages(chat_id)

# khởi listener ở bg thread
Thread(target=listener, daemon=True).start()
