from fastapi import APIRouter
from app.models import Message
from app.debounce import push_message

router = APIRouter()

@router.post("/chat")
def receive_message(message: Message):
    """
    API nhận tin nhắn từ user, gom tin nhắn để debounce.
    """
    chat_id = message.chat_id
    content = message.content
    
    push_message(
        chat_id=chat_id,
        content=content,
        debounce_ms=5000
    )
    
    return {"status": "queued", "chat_id": chat_id}
