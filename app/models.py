from pydantic import BaseModel

class Message(BaseModel):
    chat_id: str
    content: str
    # bạn có thể thêm các trường khác như timestamp, metadata...
