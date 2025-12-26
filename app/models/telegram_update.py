from pydantic import BaseModel, Field
from typing import Optional

class Chat(BaseModel):
    id: int
    type: str

class FromUser(BaseModel):
    id: int
    is_bot: bool
    first_name: Optional[str] = None
    username: Optional[str] = None

class Message(BaseModel):
    message_id: int
    from_user: FromUser = Field(alias="from")
    chat: Chat
    date: int
    text: Optional[str] = None
    
    class Config:
        populate_by_name = True  
        
class CallbackQuery(BaseModel):
    id: str
    from_user: FromUser = Field(alias="from")
    message: Optional[Message] = None
    chat_instance: str
    data: Optional[str] = None
    
    class Config:
        populate_by_name = True

class Update(BaseModel):
    update_id: int
    callback_query: Optional[CallbackQuery] = None
    message: Optional[Message] = None
    edited_message: Optional[Message] = None