"""
定义接口数据模型：和前端进行交互
继承BaseModel:在运行期间完成类型的校验和类型的转换
"""
from typing import Any

from pydantic import BaseModel

from atguigu.domain.messages import ChatHistoryMessage


class ChatObject(BaseModel):
    id : str
    title :str
    type:str
    attributes:dict[str,Any]


class ChatBotMessage(BaseModel):
    text:str
    object:ChatObject | None = None

class ChatRequest(BaseModel):
    """
    聊天请求接口数据模型
    """
    sender_id :str
    text :str | None = None
    object : ChatObject | None = None


class ChatResponse(BaseModel):
    """
    聊天响应接口数据模型
    """
    message_id :str
    messages :list[ChatBotMessage]

class ChatHistoryResponse(BaseModel):
    sender_id: str
    messages : list[ChatHistoryMessage]
