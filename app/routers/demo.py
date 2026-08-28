"""演示环境辅助接口：供配套前端页面使用。

- GET /api/v1/demo/areas   城市列表（areas.level=2），供商品搜索下拉框使用。
- GET /api/v1/demo/users   可选用户列表，供前端切换演示用户（X-User-Id）。
- GET /api/v1/demo/orders/{orderNo}  按订单号查询订单（客服演示用，无身份鉴权）。
"""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Path, Query

from ..database import fetch_all, fetch_one
from ..errors import not_found

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.get("/areas")
def list_city_areas(
    keyword: Annotated[
        str | None,
        Query(description="可选，城市名称关键字，模糊匹配。"),
    ] = None,
    limit: Annotated[
        int, Query(description="返回数量上限。", ge=1, le=500)
    ] = 200,
) -> dict:
    """返回城市级地区列表（areas.level = 2），按名称排序。"""
    sql = """
        SELECT id, area_code, area_name, area_full_name
        FROM areas
        WHERE level = 2 AND status_code = 'active'
    """
    params: list[object] = []
    if keyword:
        sql += " AND (area_name LIKE %s OR area_full_name LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    sql += " ORDER BY id ASC LIMIT %s"
    params.append(limit)
    rows = fetch_all(sql, tuple(params))
    return {
        "list": [
            {
                "areaId": row["id"],
                "areaCode": row["area_code"],
                "areaName": row["area_name"],
                "areaFullName": row["area_full_name"],
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.get("/users")
def list_demo_users(
    limit: Annotated[
        int, Query(description="返回用户数量上限。", ge=1, le=200)
    ] = 50,
) -> dict:
    """返回前 N 个非停用用户，供前端切换演示身份。"""
    rows = fetch_all(
        """
        SELECT id, nickname, phone, status_code
        FROM users
        WHERE status_code <> 'inactive'
        ORDER BY id ASC
        LIMIT %s
        """,
        (limit,),
    )
    return {
        "list": [
            {
                "userId": row["id"],
                "nickname": row["nickname"],
                "phone": row["phone"],
                "statusCode": row["status_code"],
            }
            for row in rows
        ],
        "total": len(rows),
    }


def _loads(value: Any, default: Any):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


@router.get("/orders/{orderNo}")
def get_demo_order(
    order_no: Annotated[
        str,
        Path(alias="orderNo", description="订单号，对应 orders.order_no，如 ORD0000000001。"),
    ],
) -> dict:
    """按订单号查询订单主信息与明细（客服演示用，绕过 X-User-Id 鉴权）。"""
    row = fetch_one(
        """
        SELECT o.id, o.order_no, o.order_type_code, o.status_code, o.currency_code,
               o.goods_amount, o.marketing_discount_amount, o.coupon_discount_amount,
               o.point_discount_amount, o.payable_amount, o.paid_amount,
               o.refunded_amount, o.source_channel_code, o.cancel_reason,
               o.paid_at, o.finalized_at, o.created_at,
               u.nickname, u.phone
        FROM orders o
        JOIN users u ON u.id = o.user_id
        WHERE o.order_no = %s
        """,
        (order_no,),
    )
    if row is None:
        raise not_found(f"订单 {order_no} 不存在")

    items = fetch_all(
        """
        SELECT oi.id, oi.product_type_code, oi.product_id, oi.product_name,
               oi.sale_amount, oi.status_code, oi.travel_time, oi.travel_end_time,
               oi.refunded_amount, oi.cancelled_at, oi.paid_at, oi.completed_at,
               t.traveler_name
        FROM order_items oi
        LEFT JOIN travelers t ON t.id = oi.traveler_id
        WHERE oi.order_id = %s
        ORDER BY oi.id ASC
        """,
        (row["id"],),
    )

    def _fmt_dt(v: Any) -> str | None:
        return v.strftime("%Y-%m-%d %H:%M:%S") if v is not None else None

    return {
        "orderId": row["id"],
        "orderNo": row["order_no"],
        "orderTypeCode": row["order_type_code"],
        "statusCode": row["status_code"],
        "currencyCode": row["currency_code"],
        "goodsAmount": float(row["goods_amount"]),
        "marketingDiscountAmount": float(row["marketing_discount_amount"]),
        "couponDiscountAmount": float(row["coupon_discount_amount"]),
        "pointDiscountAmount": float(row["point_discount_amount"]),
        "payableAmount": float(row["payable_amount"]),
        "paidAmount": float(row["paid_amount"]) if row["paid_amount"] is not None else None,
        "refundedAmount": float(row["refunded_amount"]) if row["refunded_amount"] is not None else None,
        "sourceChannelCode": row["source_channel_code"],
        "cancelReason": row["cancel_reason"],
        "paidAt": _fmt_dt(row["paid_at"]),
        "finalizedAt": _fmt_dt(row["finalized_at"]),
        "createdAt": _fmt_dt(row["created_at"]),
        "user": {
            "nickname": row["nickname"],
            "phone": row["phone"],
        },
        "items": [
            {
                "orderItemId": it["id"],
                "productTypeCode": it["product_type_code"],
                "productId": it["product_id"],
                "productName": it["product_name"],
                "saleAmount": float(it["sale_amount"]),
                "statusCode": it["status_code"],
                "travelTime": _fmt_dt(it["travel_time"]),
                "travelEndTime": _fmt_dt(it["travel_end_time"]),
                "refundedAmount": float(it["refunded_amount"]) if it["refunded_amount"] is not None else None,
                "travelerName": it["traveler_name"],
            }
            for it in items
        ],
    }
