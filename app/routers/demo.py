"""演示环境辅助接口：供配套前端页面使用。

- GET /api/v1/demo/areas   城市列表（areas.level=2），供商品搜索下拉框使用。
- GET /api/v1/demo/users   可选用户列表，供前端切换演示用户（X-User-Id）。
"""

from typing import Annotated

from fastapi import APIRouter, Query

from ..database import fetch_all

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
        sql += " AND area_name LIKE %s"
        params.append(f"%{keyword}%")
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
