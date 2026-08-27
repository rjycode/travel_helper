from dataclasses import dataclass,field
from typing import Any


@dataclass(slots=True)
class Command:
    command: str

    @staticmethod
    def from_dict(data: dict[str,Any]) -> "Command":
        command_type = data['command']
        clz=COMMAND_TO_CLASS[command_type]
        return clz(**data)


@dataclass(slots=True)
class StartFlowCommand(Command):
    """
    开始新的业务流程命令
    """
    flow: str


@dataclass(slots=True)
class SetSlotsCommand(Command):
    slots: dict[str,Any] = field(default_factory=dict)

@dataclass(slots=True)
class ResumedFlowCommand(Command):
    flow: str | None = None


@dataclass(slots=True)
class CancelFlowCommand(Command):
    flow: str | None = None

COMMAND_TO_CLASS: dict[str,type[Command]] = {
    "start_flow": StartFlowCommand,
    "set_slots": SetSlotsCommand,
    "resume_flow": ResumedFlowCommand,
    "cancel_flow": CancelFlowCommand
}
