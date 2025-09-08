import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_USER_NAME = os.getenv("REDIS_USER_NAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    username=REDIS_USER_NAME,
    password=REDIS_PASSWORD,
)

user_id = "1199687758"
key = f"messages:{user_id}"

msgs = r.lrange(key, 0, -1)
print(f"Number of messages: {len(msgs)}")
for idx, m in enumerate(msgs, 1):
    try:
        data = json.loads(m)
    except:
        data = m
    print(f"{idx}. {data}")
