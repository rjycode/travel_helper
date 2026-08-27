from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class TaskContext:
    flow_id: str
    step_id: str
    slots: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "slots": self.slots

        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskContext":
        return cls(
            flow_id=data['flow_id'],
            step_id=data['step_id'],
            slots=data['slots']
        )


@dataclass(slots=True)
class SystemContext:
    flow_id: str
    step_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SystemContext":
        flow_id = data['flow_id']
        clz = SYSTEM_CONTEXT_TO_CLASS[flow_id]
        return clz(**data)


@dataclass(slots=True)
class SystemTaskStartedContext(SystemContext):
    started_flow_id: str
    started_flow_name: str


@dataclass(slots=True)
class SystemTaskInterruptedContext(SystemContext):
    interrupted_flow_id: str
    interrupted_flow_name: str
    started_flow_id: str
    started_flow_name: str


@dataclass(slots=True)
class SystemTaskResumedContext(SystemContext):
    resumed_flow_id: str
    resumed_flow_name: str

@dataclass(slots=True)
class SystemTaskResumeFailedContext(SystemContext):
    """没有找到可恢复的业务流程时使用。"""


@dataclass(slots=True)
class SystemTaskCanceledContext(SystemContext):
    canceled_flow_id: str
    canceled_flow_name: str


@dataclass(slots=True)
class SystemCollectionInformationContext(SystemContext):
    response: dict[str, Any]
    slot_name: str


SYSTEM_CONTEXT_TO_CLASS: dict[str, type[SystemContext]] = {
    "system_task_started": SystemTaskStartedContext,
    "system_task_interrupted": SystemTaskInterruptedContext,
    "system_task_resumed": SystemTaskResumedContext,
    "system_task_resume_failed": SystemTaskResumeFailedContext,
    "system_task_canceled": SystemTaskCanceledContext,
    "system_collect_information": SystemCollectionInformationContext
}