from  sqlalchemy.orm import Mapped,mapped_column
from atguigu.repository.base import Base
from sqlalchemy import TEXT

class DialogueRecord(Base):
    __tablename__ = "dialogue_states"

    sender_id:Mapped[str]=mapped_column(primary_key=True)
    state_json:Mapped[str]=mapped_column(TEXT,nullable=False,default="{}")