from fastapi import FastAPI
from app.api.v1.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.redis_client import r  # để startup listener tự chạy

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origin
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (GET, POST, PUT, DELETE, ...)
    allow_headers=["*"],  # Cho phép tất cả các headers
)


# include toàn bộ router từ router.py
app.include_router(router, prefix="/api/v1", tags=["debounce-chatbot"])
