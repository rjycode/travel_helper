"""

主要管理某一个用户（sender_id）的完整对话状态：四类
1. 任务相关信息【TaskContext/SystemContext】:
2. 会话相关的信息
3. 轮次相关的信息
4. 用户点击卡片信息【FocusedObject】

8月15号 不要管谁掉。
"""
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from atguigu.domain.contexts import TaskContext, SystemContext
from atguigu.domain.messages import UserMessage, BotMessage, FocusedObject


@dataclass(slots=True)
class Turn:
    turn_id: str
    user_message: UserMessage
    bot_messages: list[BotMessage]

    def to_dict(self) -> dict[str, Any]:
        return {
            'turn_id': self.turn_id,
            'user_message': UserMessage.to_dict(self.user_message),
            "bot_messages": [BotMessage.to_dict(bot_message) for bot_message in self.bot_messages]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Turn":
        return cls(
            turn_id=data['turn_id'],
            user_message=UserMessage.from_dict(data['user_message']),
            bot_messages=[BotMessage.from_dict(bot_msg_dict) for bot_msg_dict in data['bot_messages']]
        )


@dataclass(slots=True)
class Session:
    session_id: str
    started_at: float
    activated_at: float
    closed_at: float | None = None
    turns: list[Turn] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'session_id': self.session_id,
            'started_at': self.started_at,
            'activated_at': self.activated_at,
            'closed_at': self.closed_at,
            "turns": [Turn.to_dict(turn) for turn in self.turns]

        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            session_id=data['session_id'],
            started_at=data['started_at'],
            activated_at=data['activated_at'],
            closed_at=data['closed_at'],
            turns=[Turn.from_dict(turn_dict) for turn_dict in data['turns']]
        )


@dataclass(slots=True)
class DialogueState:
    """
        超大的仓库：
        给这个大仓库放东西【分阶段来放】
        从这个大仓库拿东西【后续引擎操作时候需要的数据都从DialogueState获取】
    """
    sender_id: str
    active_task: TaskContext | None = None
    paused_tasks: list[TaskContext] = field(default_factory=list)
    active_system_task: SystemContext | None = None
    sessions: list[Session] = field(default_factory=list)
    current_session_id: str | None = None
    focused_object: FocusedObject | None = None
    pending_turn: Turn | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'sender_id': self.sender_id,
            'active_task': TaskContext.to_dict(self.active_task) if self.active_task is not None else None,
            "paused_tasks": [TaskContext.to_dict(paused_task) for paused_task in self.paused_tasks],
            "active_system_task": SystemContext.to_dict(
                self.active_system_task) if self.active_system_task is not None else None,
            "sessions": [Session.to_dict(session) for session in self.sessions],
            "current_session_id": self.current_session_id,
            "focused_object": FocusedObject.to_dict(self.focused_object) if self.focused_object is not None else None,
            "pending_turn": Turn.to_dict(self.pending_turn) if self.pending_turn is not None else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DialogueState":
        return cls(
            sender_id=data['sender_id'],
            active_task=TaskContext.from_dict(data['active_task']) if data['active_task'] is not None else None,
            paused_tasks=[TaskContext.from_dict(paused_task) for paused_task in data['paused_tasks']],
            active_system_task=SystemContext.from_dict(data['active_system_task']) if data[
                                                                                          'active_system_task'] is not None else None,
            sessions=[Session.from_dict(session_dict) for session_dict in data['sessions']],
            current_session_id=data['current_session_id'],
            focused_object=FocusedObject.from_dict(data['focused_object']) if data[
                                                                                  'focused_object'] is not None else None,
            pending_turn=Turn.from_dict(data['pending_turn']) if data['pending_turn'] is not None else None

        )

    ################################################任务相关方法########################################################
    def start_task(self, task_context: TaskContext):
        """
        职责：启动业务流程任务
        :param task_context:
        :return:
        """
        self.active_task = task_context

    def end_active_task(self):
        """
        职责：结束业务流程任务
        :return:
        """
        self.active_task = None

    def cancel_active_task(self):
        """
        职责：取消正在执行的业务流程、系统流程任务
        :return:
        """
        self.active_task = None
        self.active_system_task = None

    def remove_paused_tasks(self, flow_id: str):
        """
        职责：移除暂停业务流程任务栈中的业务流程
        :param flow_id:
        :return:
        """
        self.paused_tasks = [paused_task for paused_task in self.paused_tasks if paused_task.flow_id != flow_id]

    def interrupt_active_task(self):
        """
        职责：中断正在执行的业务流程任务
        :return:
        """
        self.paused_tasks.append(self.active_task)
        self.active_task = None

    def resume_task(self, flow_id: str | None = None):
        """
        职责：恢复暂停业务流程任务栈中的业务流程
        :param flow_id:
        :return:
        """
        if not self.paused_tasks:
            return False

        if flow_id is None:
            paused_task = self.paused_tasks.pop()
            self.active_task = paused_task
            return True

        for index, paused_task in enumerate(self.paused_tasks):
            if paused_task.flow_id == flow_id:
                self.active_task = paused_task
                del self.paused_tasks[index]
                return True

        return False

    def start_system_task(self, system_task: SystemContext):
        self.active_system_task = system_task


    def end_system_task(self):
        self.active_system_task = None

    def current_task(self):

        """
        调用者：流程推进器（使用）
        职责：返回的任务流程上下文可能是系统流程任务上下文也可能是业务流程任务上下文 也可能是None
        ①业务流程任务上下文
        ②系统流程任务上下文
        case1: ① ② 都有，优先返回②（也即系统流程任务上下文） 原因：系统流程的过场白先返回
        case2: ① ② 都没有，返回None
        case3: ①有，②没有，返回①
        case4: ②有，①没有，返回②
        结论：谁有返回谁，都有返回系统流程任务上下文。

        Returns:
        """
        return self.active_system_task or self.active_task

    ################################################槽位相关方法########################################################
    def set_slots(self,slot_info: dict[str, Any]):
        if self.active_task is not None:
            self.active_task.slots.update(slot_info)


    def remove_slots(self,slot_name: str):
        if self.active_task is not None:
            self.active_task.slots.pop(slot_name)

    ################################################会话相关方法########################################################
    def start_session(self):
        """
        职责：创建session对象 给session对象的属性赋值

        :return:
        """
        now = time.time()
        session = Session(session_id=str(uuid4().hex),started_at=now,activated_at=now)

        self.current_session_id = session.session_id

        self.sessions.append(session)

    def current_session(self) -> Session | None:
        """
        职责：返回当前session
        :return:
        """

        for session in self.sessions:
            if session.session_id == self.current_session_id:
                return session

        return None

    def close_current_session(self):
        """
        职责：更新当前session对象的closed_at属性 以及情况current_session_id
        :return:
        """
        self.current_session().closed_at = time.time()
        self.current_session_id = None

    def reset_runtime_state_for_new_session(self):
        """
        职责：当前的session超时，会把超时的这个session之前的对话状态清空（判断session超时的规则）

        :return:
        """
        self.active_task = None
        self.active_system_task = None
        self.paused_tasks = []

        self.focused_object = None

        self.pending_turn = None

    ################################################轮次相关方法########################################################
    def begin_turn(self,user_message: UserMessage):
        """
        职责：实例化turn对象
        :param user_message:
        :return:
        """
        turn = Turn(turn_id=str(uuid4().hex),user_message=user_message,bot_messages=[])

        self.pending_turn = turn

    def commit_pending_turn(self):
        """
        职责：将缓存区的内容更新到当前的session中 并且清空缓冲区
        :return:
        """
        self.current_session().turns.append(self.pending_turn)

        self.pending_turn = None

    ################################################对象相关方法########################################################
    def set_focused_object(self, object: FocusedObject):
        """
        职责：将点击的卡片对象的信息更新到focused_object
        :param object:
        :return:
        """
        self.focused_object = object





