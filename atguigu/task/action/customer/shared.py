"""
封装自定义action统一发请求的工具函数
"""



from urllib.parse import quote
from atguigu.config.settings import settings
from atguigu.infrastructure import http_client


def _base_url() -> str:
    """
    职责：获取中台服务的地址
    Returns:

    """
    return settings.commerce_api_base_url.rstrip("/")


def _extract_data(result: dict | None) -> dict | None:
    """
    职责：从响应结果中获取真实的字典数据
    Args:
        result:

    Returns:

    """
    data = result.get("data") if isinstance(result, dict) else None
    return data if isinstance(data, dict) else None


async def fetch_order(order_id: str) -> dict | None:
    """
    职责：根据订单ID 获取订单的数据
    Args:
        order_id:

    Returns:

    """
    try:
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id)}")
        return _extract_data(r.json())
    except Exception:
        return None


async def fetch_logistics(order_id: str) -> dict | None:
    """
     职责：根据订单ID 获取订单物流的数据
    Args:
        order_id:

    Returns:

    """
    try:
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id)}/logistics")
        return _extract_data(r.json())
    except Exception:
        return None


async def fetch_product(product_id: str) -> dict | None:
    """
    职责： 根据商品ID 获取商品的数据
    Args:
        product_id:

    Returns:

    """
    try:
        r = await http_client.http_client.get(f"{_base_url()}/products/{quote(product_id)}")
        return _extract_data(r.json())
    except Exception:
        return None


# ============ 旅游平台（travel-data）查询 ============

def _travel_base_url() -> str:
    """旅游平台数据服务地址（travel-data 后端）。"""
    return settings.travel_api_base_url.rstrip("/")


def _extract_list(result: dict | None) -> list[dict]:
    """travel-data 接口统一返回 {\"list\": [...]}，这里直接取 list。"""
    if not isinstance(result, dict):
        return []
    data = result.get("list")
    return data if isinstance(data, list) else []


async def fetch_city_area_id(city_name: str) -> int | None:
    """根据城市名（如 上海/北京）查 areas.id，用于 travel-data 搜索接口。"""
    if not city_name:
        return None
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/demo/areas", params={"keyword": city_name}
        )
        items = _extract_list(r.json())
        if not items:
            return None
        # 优先精确匹配城市名（如 北京市），否则取第一个模糊命中
        for item in items:
            full = item.get("areaFullName") or ""
            if item.get("areaName") == city_name or city_name in full:
                return int(item["areaId"])
        return int(items[0]["areaId"])
    except Exception:
        return None


async def fetch_flights(departure_area_id: int, arrival_area_id: int, departure_date: str) -> list[dict]:
    """查询机票：出发城市→到达城市→日期，返回航班列表。"""
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/flights/search",
            params={
                "departureAreaId": departure_area_id,
                "arrivalAreaId": arrival_area_id,
                "departureDate": departure_date,
            },
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_hotels(area_id: int, check_in_date: str, check_out_date: str) -> list[dict]:
    """查询酒店：城市→入住→离店，返回酒店列表。"""
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/hotels",
            params={
                "areaId": area_id,
                "checkInDate": check_in_date,
                "checkOutDate": check_out_date,
            },
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_scenic_spots(area_id: int, travel_date: str) -> list[dict]:
    """查询景点：城市→游玩日期，返回景点列表。"""
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/scenic-spots",
            params={"areaId": area_id, "travelDate": travel_date},
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_trains(departure_area_id: int, arrival_area_id: int, departure_date: str) -> list[dict]:
    """查询火车票：出发城市→到达城市→日期，返回车次列表。"""
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/trains/search",
            params={
                "departureAreaId": departure_area_id,
                "arrivalAreaId": arrival_area_id,
                "departureDate": departure_date,
            },
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_buses(departure_area_id: int, arrival_area_id: int, departure_date: str) -> list[dict]:
    """查询汽车票：出发城市→到达城市→日期，返回班车列表。"""
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/buses/search",
            params={
                "departureAreaId": departure_area_id,
                "arrivalAreaId": arrival_area_id,
                "departureDate": departure_date,
            },
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_transfers(area_id: int, business_date: str) -> list[dict]:
    """查询接送服务：城市→日期，返回服务列表。"""
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/transfers",
            params={"areaId": area_id, "businessDate": business_date},
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_travel_order(order_no: str) -> dict | None:
    """按订单号查询旅游订单（含明细）。"""
    if not order_no:
        return None
    try:
        r = await http_client.http_client.get(
            f"{_travel_base_url()}/api/v1/demo/orders/{quote(order_no)}"
        )
        data = r.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def create_travel_refund(order_no: str, reason: str) -> dict | None:
    """按订单号发起退款申请（客服演示）。"""
    if not order_no:
        return None
    try:
        r = await http_client.http_client.post(
            f"{_travel_base_url()}/api/v1/demo/refunds",
            json={"orderNo": order_no, "reason": reason},
        )
        data = r.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def create_work_order(ticket_type_code: str, title: str, description: str, order_no: str | None = None) -> dict | None:
    """提交客服工单。"""
    try:
        r = await http_client.http_client.post(
            f"{_travel_base_url()}/api/v1/demo/work-orders",
            json={
                "ticketTypeCode": ticket_type_code,
                "title": title,
                "description": description,
                "orderNo": order_no,
            },
        )
        data = r.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None