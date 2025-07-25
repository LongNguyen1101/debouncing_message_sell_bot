from fastapi import FastAPI
from app.router import router
from app.redis_client import r  # để startup listener tự chạy

app = FastAPI()

# include toàn bộ router từ router.py
app.include_router(router, prefix="/api/v1", tags=["debounce-chatbot"])
