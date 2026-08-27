from dataclasses import dataclass,field

from atguigu.task.flows.steps import FlowStep

@dataclass(slots=True)
class FlowSlot:
    slot_name: str
    type: str
    label: str
    description: str


@dataclass(slots=True)
class Flow:
    """
    流程对象（不区分系统流程 业务流程）
    作用1：后续流程推进器使用流程（steps）
    作用2：后续LLM作为参考，选择开启哪一个业务流程 取消 恢复 填写槽位信息[slots]

    """
    id: str
    name:str
    description: str
    steps: list[FlowStep]
    slots: dict[str,FlowSlot]=field(default_factory=dict)


    def get_step_by_id(self,step_id: str) -> FlowStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step

        return None


@dataclass(slots=True)
class FlowList:
    """
    职责：承载yaml文件中的顶层元素（slots：user_flows.yml中/flows:两份yml文件都有）

    """
    flows: list[Flow]
    slots: dict[str,FlowSlot] = field(default_factory=dict)


    def get_flow_by_id(self,flow_id: str) -> Flow | None:

        for flow in self.flows:
            if flow.id == flow_id:
                return flow

        return None
