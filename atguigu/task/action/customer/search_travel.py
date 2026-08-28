"""
旅游平台查询 Action：机票搜索、酒店搜索。

通过调用 travel-data 后端（/api/v1/flights/search、/api/v1/hotels）查询
真实库存与价格，结果格式化后写入 slots，由 action_response 渲染给用户。
"""

from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.customer.shared import (
    fetch_buses,
    fetch_city_area_id,
    fetch_flights,
    fetch_hotels,
    fetch_scenic_spots,
    fetch_trains,
    fetch_transfers,
    fetch_travel_order,
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


class ActionSearchScenicSpots(Action):
    """搜索景点：根据城市、游玩日期查询景点。"""

    name = "action_search_scenic_spots"

    async def run(self, action_kwargs, state):
        city = (state.active_task.slots.get("scenic_city") or "").strip()
        travel_date = (state.active_task.slots.get("scenic_date") or "").strip()

        area_id = await fetch_city_area_id(city)
        if area_id is None:
            return ActionResult(updated_slots={
                "scenic_results": f"抱歉，暂时无法识别城市「{city}」，请确认城市名称后重试。",
            })

        spots = await fetch_scenic_spots(area_id, travel_date)
        if not spots:
            return ActionResult(updated_slots={
                "scenic_results": f"{travel_date} 在 {city} 暂无可预订的景点。",
            })

        lines = [f"为你找到 {city} {travel_date} 可游玩的景点："]
        for s in spots[:3]:
            lines.append(
                f"· {s['scenicName']}（{s['ratingCode']}）"
                f"¥{s['minSalePriceAmount']}/张起，开放 {s['openTime']}-{s['closeTime']}"
            )
        if len(spots) > 3:
            lines.append(f"……共 {len(spots)} 个景点，可进一步筛选。")

        return ActionResult(updated_slots={"scenic_results": chr(10).join(lines)})


class ActionSearchTrains(Action):
    """搜索火车票：根据出发/到达城市、日期查询车次。"""

    name = "action_search_trains"

    async def run(self, action_kwargs, state):
        departure_city = (state.active_task.slots.get("train_from") or "").strip()
        arrival_city = (state.active_task.slots.get("train_to") or "").strip()
        departure_date = (state.active_task.slots.get("train_date") or "").strip()

        dep_id = await fetch_city_area_id(departure_city)
        arr_id = await fetch_city_area_id(arrival_city)
        if dep_id is None or arr_id is None:
            return ActionResult(updated_slots={
                "train_results": f"抱歉，暂时无法识别城市「{departure_city if dep_id is None else arrival_city}」，请确认后重试。",
            })

        trains = await fetch_trains(dep_id, arr_id, departure_date)
        if not trains:
            return ActionResult(updated_slots={
                "train_results": f"{departure_date} 从 {departure_city} 到 {arrival_city} 暂无可售车次。",
            })

        lines = [f"为你找到 {departure_city} → {arrival_city} {departure_date} 的车次："]
        for t in trains[:3]:
            lines.append(
                f"· {t['trainNo']}：{t['departureTime'][11:16]} 发车（{t['departureHubName']}）→ "
                f"{t['arrivalTime'][11:16]} 到达（{t['arrivalHubName']}），最低价 ¥{t['minSalePriceAmount']} 起"
            )
        if len(trains) > 3:
            lines.append(f"……共 {len(trains)} 个车次，可进一步筛选。")

        return ActionResult(updated_slots={"train_results": chr(10).join(lines)})


class ActionSearchBuses(Action):
    """搜索汽车票：根据出发/到达城市、日期查询班车。"""

    name = "action_search_buses"

    async def run(self, action_kwargs, state):
        departure_city = (state.active_task.slots.get("bus_from") or "").strip()
        arrival_city = (state.active_task.slots.get("bus_to") or "").strip()
        departure_date = (state.active_task.slots.get("bus_date") or "").strip()

        dep_id = await fetch_city_area_id(departure_city)
        arr_id = await fetch_city_area_id(arrival_city)
        if dep_id is None or arr_id is None:
            return ActionResult(updated_slots={
                "bus_results": f"抱歉，暂时无法识别城市「{departure_city if dep_id is None else arrival_city}」，请确认后重试。",
            })

        buses = await fetch_buses(dep_id, arr_id, departure_date)
        if not buses:
            return ActionResult(updated_slots={
                "bus_results": f"{departure_date} 从 {departure_city} 到 {arrival_city} 暂无可售班车。",
            })

        lines = [f"为你找到 {departure_city} → {arrival_city} {departure_date} 的班车："]
        for b in buses[:3]:
            lines.append(
                f"· {b['routeName']}：{b['departureTime'][11:16]} 发车（{b['departureHubName']}）→ "
                f"{b['arrivalTime'][11:16]} 到达（{b['arrivalHubName']}），票价 ¥{b['salePriceAmount']}"
            )
        if len(buses) > 3:
            lines.append(f"……共 {len(buses)} 个班次，可进一步筛选。")

        return ActionResult(updated_slots={"bus_results": chr(10).join(lines)})


class ActionSearchTransfers(Action):
    """搜索接送服务：根据城市、日期查询。"""

    name = "action_search_transfers"

    async def run(self, action_kwargs, state):
        city = (state.active_task.slots.get("transfer_city") or "").strip()
        business_date = (state.active_task.slots.get("transfer_date") or "").strip()

        area_id = await fetch_city_area_id(city)
        if area_id is None:
            return ActionResult(updated_slots={
                "transfer_results": f"抱歉，暂时无法识别城市「{city}」，请确认城市名称后重试。",
            })

        services = await fetch_transfers(area_id, business_date)
        if not services:
            return ActionResult(updated_slots={
                "transfer_results": f"{business_date} 在 {city} 暂无可预订的接送服务。",
            })

        lines = [f"为你找到 {city} {business_date} 的接送服务："]
        for s in services[:3]:
            lines.append(
                f"· {s['serviceName']}（{s['vehicleTypeCode']}，载客 {s['passengerCapacity']} 人），"
                f"可售 {s['availableInventory']} 单"
            )
        if len(services) > 3:
            lines.append(f"……共 {len(services)} 个服务，可进一步筛选。")

        return ActionResult(updated_slots={"transfer_results": chr(10).join(lines)})


ORDER_STATUS_MAP = {
    "pending_payment": "待支付",
    "cancelled": "已取消",
    "paid": "已支付",
    "in_progress": "进行中",
    "finished": "已完成",
}
PRODUCT_TYPE_MAP = {
    "hotel_room": "酒店",
    "scenic_ticket": "景点门票",
    "flight_cabin": "机票",
    "train_seat": "火车票",
    "bus_seat": "汽车票",
    "transfer_service": "接送服务",
}


class ActionLookupTravelOrder(Action):
    """查询旅游订单：根据订单号查询状态与出行信息。"""

    name = "action_lookup_travel_order"

    async def run(self, action_kwargs, state):
        order_no = (state.active_task.slots.get("travel_order_no") or "").strip()

        order = await fetch_travel_order(order_no)
        if order is None:
            return ActionResult(updated_slots={
                "order_results": f"抱歉，没有查到订单 {order_no} 的信息，请确认订单号是否正确。",
            })

        status = ORDER_STATUS_MAP.get(order.get("statusCode"), order.get("statusCode"))
        product_type = PRODUCT_TYPE_MAP.get(order.get("orderTypeCode"), order.get("orderTypeCode"))
        lines = [
            f"订单 {order['orderNo']}（{product_type}）当前状态：{status}。",
        ]
        if order.get("payableAmount") is not None:
            lines.append(f"订单金额 ¥{order['payableAmount']}"
                         + (f"，已支付 ¥{order['paidAmount']}" if order.get("paidAmount") is not None else ""))
        items = order.get("items") or []
        if items:
            first = items[0]
            detail = f"产品：{first.get('productName')}"
            if first.get("travelTime"):
                detail += f"，出行时间 {first['travelTime']}"
            if first.get("travelerName"):
                detail += f"，出行人 {first['travelerName']}"
            lines.append(detail)
            if len(items) > 1:
                lines.append(f"共 {len(items)} 条明细。")
        if order.get("cancelReason"):
            lines.append(f"取消原因：{order['cancelReason']}")

        return ActionResult(updated_slots={"order_results": chr(10).join(lines)})
