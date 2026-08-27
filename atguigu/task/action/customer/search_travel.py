"""
旅游平台查询 Action：机票搜索、酒店搜索。

通过调用 travel-data 后端（/api/v1/flights/search、/api/v1/hotels）查询
真实库存与价格，结果格式化后写入 slots，由 action_response 渲染给用户。
"""

from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.shared import (
    fetch_city_area_id,
    fetch_flights,
    fetch_hotels,
)


class ActionSearchFlights(Action):
    """搜索机票：根据出发城市、到达城市、出发日期查询航班。"""

    name = "action_search_flights"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        # 1. 读取槽位
        departure_city = (state.active_task.slots.get("departure_city") or "").strip()
        arrival_city = (state.active_task.slots.get("arrival_city") or "").strip()
        departure_date = (state.active_task.slots.get("departure_date") or "").strip()

        # 2. 城市名 -> areas.id
        dep_id = await fetch_city_area_id(departure_city)
        arr_id = await fetch_city_area_id(arrival_city)

        if dep_id is None or arr_id is None:
            return ActionResult(updated_slots={
                "flight_results": f"抱歉，暂时无法识别城市「{departure_city if dep_id is None else arrival_city}」，"
                                  f"请确认城市名称后重试。",
            })

        # 3. 查询航班
        flights = await fetch_flights(dep_id, arr_id, departure_date)
        if not flights:
            return ActionResult(updated_slots={
                "flight_results": f"{departure_date} 从 {departure_city} 到 {arrival_city} 暂无可售航班。",
            })

        # 4. 格式化结果（最多展示 3 班）
        lines = [f"为你找到 {departure_city} → {arrival_city} {departure_date} 的航班："]
        for f in flights[:3]:
            lines.append(
                f"· {f['airlineCode']} {f['flightNo']}：{f['departureTime'][11:16]} 起飞"
                f"（{f['departureHubName']}）→ {f['arrivalTime'][11:16]} 到达"
                f"（{f['arrivalHubName']}），最低价 ¥{f['minSalePriceAmount']} 起"
            )
        if len(flights) > 3:
            lines.append(f"……共 {len(flights)} 个航班，可进一步筛选。")

        return ActionResult(updated_slots={"flight_results": "\n".join(lines)})


class ActionSearchHotels(Action):
    """搜索酒店：根据城市、入住日期、离店日期查询酒店。"""

    name = "action_search_hotels"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        # 1. 读取槽位
        city = (state.active_task.slots.get("hotel_city") or "").strip()
        check_in = (state.active_task.slots.get("check_in_date") or "").strip()
        check_out = (state.active_task.slots.get("check_out_date") or "").strip()

        # 2. 城市名 -> areas.id
        area_id = await fetch_city_area_id(city)
        if area_id is None:
            return ActionResult(updated_slots={
                "hotel_results": f"抱歉，暂时无法识别城市「{city}」，请确认城市名称后重试。",
            })

        # 3. 查询酒店
        hotels = await fetch_hotels(area_id, check_in, check_out)
        if not hotels:
            return ActionResult(updated_slots={
                "hotel_results": f"{check_in} 至 {check_out} 在 {city} 暂无可订酒店。",
            })

        # 4. 格式化结果（最多展示 3 家）
        lines = [f"为你找到 {city} {check_in} 至 {check_out} 的酒店："]
        for h in hotels[:3]:
            lines.append(
                f"· {h['hotelName']}（{'★' * int(h['starRatingCode'])}）"
                f"¥{h['minSalePriceAmount']}/晚起，可售 {h['availableRoomCount']} 间"
            )
        if len(hotels) > 3:
            lines.append(f"……共 {len(hotels)} 家酒店，可进一步筛选。")

        return ActionResult(updated_slots={"hotel_results": "\n".join(lines)})
