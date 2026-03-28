import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.database import init_db
from scheduler.jobs import start_scheduler
from api.websocket import manager
from api.routes import market, strategy, backtest, trading, portfolio, alerts
from exchange.delta_websocket import DeltaWebSocket
from data.ticker import update_ticker


async def on_ws_message(msg: dict):
    msg_type = msg.get("type", "")
    if msg_type in ("v2/ticker", "ticker"):
        symbol = msg.get("symbol") or (msg.get("result") or {}).get("symbol")
        if symbol:
            update_ticker(symbol, msg.get("result", msg))
            await manager.broadcast({"type": "ticker", "symbol": symbol,
                                     "data": msg.get("result", msg)})


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    delta_ws = DeltaWebSocket(on_ws_message)
    await delta_ws.subscribe([
        {"name": "v2/ticker", "symbols": ["BTCUSD", "ETHUSD", "SOLUSD"]},
    ])
    ws_task = asyncio.create_task(delta_ws.connect())
    yield
    ws_task.cancel()


app = FastAPI(title="Delta Algo Trading Platform", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")

app.include_router(market.router)
app.include_router(strategy.router)
app.include_router(backtest.router)
app.include_router(trading.router)
app.include_router(portfolio.router)
app.include_router(alerts.router)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    from config import settings
    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=True)
