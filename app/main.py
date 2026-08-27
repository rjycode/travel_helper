from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import APP_PORT
from .routers.demo import router as demo_router
from .routers.marketing import router as marketing_router
from .routers.orders import router as orders_router
from .routers.products import router as products_router
from .routers.refunds import router as refunds_router
from .routers.users import router as users_router

OPENAPI_TAGS = [
    {"name": "users", "description": "1. 用户中心与会员信息"},
    {"name": "products", "description": "2. 商品搜索、详情与价格查询"},
    {"name": "marketing", "description": "3. 营销与优惠券"},
    {"name": "orders", "description": "4. 交易、订单与支付"},
    {"name": "refunds", "description": "5. 售后与退款"},
    {"name": "demo", "description": "6. 演示环境辅助接口（配套前端使用）"},
]

app = FastAPI(title="Travel Data API", version="0.1.0", openapi_tags=OPENAPI_TAGS)

app.include_router(users_router)
app.include_router(products_router)
app.include_router(marketing_router)
app.include_router(orders_router)
app.include_router(refunds_router)
app.include_router(demo_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.exception_handler(ValueError)
async def handle_value_error(_, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=APP_PORT, reload=False)
