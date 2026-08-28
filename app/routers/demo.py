"""演示环境辅助接口：供配套前端页面使用。

- GET /api/v1/demo/areas   城市列表（areas.level=2），供商品搜索下拉框使用。
- GET /api/v1/demo/users   可选用户列表，供前端切换演示用户（X-User-Id）。
- GET /api/v1/demo/orders/{orderNo}  按订单号查询订单（客服演示用，无身份鉴权）。
- POST /api/v1/demo/refunds  按订单号发起退款申请（客服演示用）。
- POST /api/v1/demo/work-orders  提交客服工单（需求说明 §4.5）。
"""

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from pydantic import BaseModel, Field

from ..database import db_cursor, fetch_all, fetch_one
from ..errors import bad_request, conflict, not_found
from ..utils import LOCAL_TZ, make_no, money

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


class RefundRequestCreate(BaseModel):
    """客服退款申请请求体（演示用）。"""

    orderNo: str = Field(description="订单号，如 ORD0000000001。")
    reason: str = Field(default="行程变更", description="退款原因。")
    requestedAmount: float | None = Field(
        default=None, description="申请退款金额，不传则按明细剩余可退金额全额申请。"
    )


@router.post("/refunds")
def create_demo_refund(body: RefundRequestCreate) -> dict:
    """按订单号发起退款申请（客服演示，绕过 X-User-Id 鉴权）。

    选择订单下第一笔状态为 paid/ticketed/completed 且未全额退款的明细，
    以其剩余可退金额为上限创建退款申请。
    """
    order = fetch_one(
        "SELECT id, user_id, order_no, status_code FROM orders WHERE order_no = %s",
        (body.orderNo,),
    )
    if order is None:
        raise not_found(f"订单 {body.orderNo} 不存在")
    if order["status_code"] not in ("paid", "in_progress", "finished"):
        raise conflict(f"订单当前状态（{order['status_code']}）不允许申请退款")

    item = fetch_one(
        """
        SELECT id, sale_amount, status_code
        FROM order_items
        WHERE order_id = %s AND status_code IN ('paid', 'ticketed', 'completed')
        ORDER BY id ASC
        LIMIT 1
        """,
        (order["id"],),
    )
    if item is None:
        raise conflict("该订单没有可退款的明细")

    # 已成功退款金额
    refunded = fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM refund_records
        WHERE order_item_id = %s AND status_code = 'success'
        """,
        (item["id"],),
    )
    refunded_amount = float(refunded["total"]) if refunded else 0.0
    remaining = float(item["sale_amount"]) - refunded_amount
    if remaining <= 0:
        raise conflict("该订单明细已全额退款，无可退金额")

    amount = remaining if body.requestedAmount is None else body.requestedAmount
    if amount <= 0:
        raise bad_request("申请退款金额必须大于 0")
    if amount > remaining:
        raise conflict(f"申请金额超过可退金额（剩余 {money(remaining)}）")

    # 存在进行中的退款申请则不重复创建
    in_progress = fetch_one(
        """
        SELECT id FROM refund_requests
        WHERE order_item_id = %s AND status_code IN ('pending', 'approved')
        LIMIT 1
        """,
        (item["id"],),
    )
    if in_progress is not None:
        raise conflict("该订单明细存在进行中的退款申请")

    now = datetime.now(LOCAL_TZ)
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO refund_requests (
                refund_request_no, order_id, order_item_id, user_id, requested_amount,
                approved_amount, status_code, requested_at, processed_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, NULL, 'pending', %s, NULL, %s, %s)
            """,
            (make_no("RR"), order["id"], item["id"], order["user_id"], amount, now, now, now),
        )
        refund_request_id = cursor.lastrowid

    return {
        "refundRequestId": refund_request_id,
        "refundRequestNo": f"RR{refund_request_id:012d}",
        "orderNo": order["order_no"],
        "orderItemId": item["id"],
        "requestedAmount": money(amount),
        "reason": body.reason,
        "statusCode": "pending",
        "requestedAt": now.strftime("%Y-%m-%d %H:%M:%S"),
    }


class WorkOrderCreate(BaseModel):
    """客服工单请求体（演示用）。"""

    ticketTypeCode: str = Field(description="工单类型：after_sale/complaint/refund/consult。")
    title: str = Field(description="工单标题。")
    description: str = Field(description="问题描述。")
    orderNo: str | None = Field(default=None, description="关联订单号（可选）。")


@router.post("/work-orders")
def create_work_order(body: WorkOrderCreate) -> dict:
    """提交客服工单（需求说明 §4.5：收集工单类型 → 关联订单号 → 问题描述 → 创建工单）。"""
    valid_types = {"after_sale", "complaint", "refund", "consult"}
    if body.ticketTypeCode not in valid_types:
        raise bad_request(f"ticketTypeCode 必须为 {sorted(valid_types)} 之一")
    title = body.title.strip()
    description = body.description.strip()
    if not title:
        raise bad_request("title 不能为空")
    if not description:
        raise bad_request("description 不能为空")

    now = datetime.now(LOCAL_TZ)
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO work_orders (
                work_order_no, user_id, order_no, ticket_type_code,
                title, description, status_code, created_at, updated_at
            ) VALUES (%s, NULL, %s, %s, %s, %s, 'open', %s, %s)
            """,
            (make_no("WO"), body.orderNo, body.ticketTypeCode, title, description, now, now),
        )
        work_order_id = cursor.lastrowid

    return {
        "workOrderId": work_order_id,
        "workOrderNo": f"WO{work_order_id:012d}",
        "ticketTypeCode": body.ticketTypeCode,
        "title": title,
        "description": description,
        "orderNo": body.orderNo,
        "statusCode": "open",
        "createdAt": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
