from atguigu.chitchat.responder import ChitChatResponder
from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState


class ChitChatHandler:


    def __init__(self, chitchat_responder: ChitChatResponder):
        self._chitchat_responder = chitchat_responder

    async def handle(self,
                      chat: str,
                      state: DialogueState) -> list[BotMessage]:

        bot_messages = await self._chitchat_responder.response(chat,state)

        return bot_messages
