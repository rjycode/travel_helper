from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.chat_history.builder import ChatHistoryBuilder
from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure.llm_client import llm_client
from atguigu.prompt.loader import load_prompt_template_content


class ChitChatResponder:

    async def response(self, chat:str , state:DialogueState) -> list[BotMessage]:

        prompt_template_str = load_prompt_template_content("chitchat_respond")

        prompt_template = PromptTemplate.from_template(template=prompt_template_str,template_format="jinja2")

        chain = prompt_template | llm_client | StrOutputParser()

        result = await chain.ainvoke({
            "user_message": chat,
            "history": ChatHistoryBuilder.build(state.current_session().turns[-10:])
        })

        return [BotMessage(text=result)]

