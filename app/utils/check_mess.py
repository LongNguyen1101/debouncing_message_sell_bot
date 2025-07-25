import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
user_id = "123"
key = f"messages:{user_id}"

msgs = r.lrange(key, 0, -1)
print(f"Number of messages: {len(msgs)}")
for idx, m in enumerate(msgs, 1):
    try:
        data = json.loads(m)
    except:
        data = m
    print(f"{idx}. {data}")
