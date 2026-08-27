"""
消息的类型有几种：
1. 用户角色的消息
2. 机器人角色回复的消息


不管是进行网络传输或者是进行IO读写：永远都不能直接操作"对象" 对象是内存中的。



"""
from enum import Enum
from typing import Any, Literal
from dataclasses import dataclass


class MessageType(Enum):
    TEXT = "text"
    OBJECT = "object"


@dataclass(slots=True)
class FocusedObject:
    id: str
    title: str
    type: str
    attributes: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "attributes": self.attributes
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FocusedObject":
        return cls(
            id=data['id'],
            title=data['title'],
            type=data['type'],
            attributes=data['attributes']
        )


@dataclass(slots=True)
class UserMessage:
    sender_id: str
    message_id: str
    type: MessageType
    text: str | None = None
    object: FocusedObject | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "message_id": self.message_id,
            "type": self.type.value,
            "text": self.text,
            "object": FocusedObject.to_dict(self.object) if self.object is not None else None

        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserMessage":
        return cls(
            sender_id=data['sender_id'],
            message_id=data['message_id'],
            type=MessageType(data['type']),
            text=data['text'],
            object=FocusedObject.from_dict(data['object']) if data['object'] is not None else None
        )


@dataclass(slots=True)
class BotMessage:
    text: str
    object: FocusedObject | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "object": FocusedObject.to_dict(self.object) if self.object is not None else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BotMessage":
        return cls(
            text=data['text'],
            object=FocusedObject.from_dict(data['object']) if data['object'] is not None else None
        )

@dataclass(slots=True)
class ProcessedResult:
    message_id :str
    messages : list[BotMessage]


@dataclass(slots=True)
class ChatHistoryMessage:
    session_id: str
    role: Literal["user", "bot"]
    text: str | None = None
    object: FocusedObject | None = None
