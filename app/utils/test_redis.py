import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_USER_NAME = os.getenv("REDIS_USER_NAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        username=REDIS_USER_NAME,
        password=REDIS_PASSWORD,
    )

    print("Ping response:", r.ping())
except Exception as e:
    print("Could not connect redis:", e)