import redis
try:
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    print("Ping response:", r.ping())
except Exception as e:
    print("Could not connect redis:", e)