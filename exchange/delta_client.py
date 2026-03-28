import httpx
import time
from typing import Optional
from config import settings
from core.security import generate_signature


class DeltaClient:
    def __init__(self):
        self.base_url = settings.delta_base_url
        self.client = httpx.AsyncClient(timeout=15.0)

    async def _get(self, path: str, params: dict = None) -> dict:
        url = self.base_url + path
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _auth_get(self, path: str, params: dict = None) -> dict:
        query_string = ""
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
        headers = generate_signature("GET", path, query_string)
        url = self.base_url + path
        resp = await self.client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def _auth_post(self, path: str, body: dict) -> dict:
        import json
        body_str = json.dumps(body)
        headers = generate_signature("POST", path, "", body_str)
        url = self.base_url + path
        resp = await self.client.post(url, content=body_str, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def _auth_delete(self, path: str, body: dict = None) -> dict:
        import json
        body_str = json.dumps(body or {})
        headers = generate_signature("DELETE", path, "", body_str)
        url = self.base_url + path
        resp = await self.client.request("DELETE", url, content=body_str, headers=headers)
        resp.raise_for_status()
        return resp.json()

    # ── Public Endpoints ──────────────────────────────────────────────────────

    async def get_products(self) -> list:
        data = await self._get("/v2/products")
        return data.get("result", [])

    async def get_candles(self, symbol: str, resolution: str, start: int, end: int) -> list:
        data = await self._get("/v2/history/candles", params={
            "symbol": symbol,
            "resolution": resolution,
            "start": start,
            "end": end,
        })
        return data.get("result", [])

    async def get_ticker(self, symbol: str) -> dict:
        data = await self._get(f"/v2/tickers/{symbol}")
        return data.get("result", {})

    async def get_tickers(self) -> list:
        data = await self._get("/v2/tickers")
        return data.get("result", [])

    async def get_orderbook(self, symbol: str, depth: int = 10) -> dict:
        data = await self._get(f"/v2/l2orderbook/{symbol}", params={"depth": depth})
        return data.get("result", {})

    # ── Private Endpoints ─────────────────────────────────────────────────────

    async def get_wallet_balance(self) -> list:
        data = await self._auth_get("/v2/wallet/balances")
        return data.get("result", [])

    async def get_positions(self) -> list:
        data = await self._auth_get("/v2/positions/margined")
        return data.get("result", [])

    async def get_open_orders(self, symbol: str = None) -> list:
        params = {}
        if symbol:
            params["product_symbol"] = symbol
        data = await self._auth_get("/v2/orders", params=params)
        return data.get("result", [])

    async def place_order(self, symbol: str, side: str, size: float,
                          order_type: str = "market_order",
                          limit_price: float = None) -> dict:
        body = {
            "product_symbol": symbol,
            "side": side,
            "size": size,
            "order_type": order_type,
        }
        if limit_price:
            body["limit_price"] = str(limit_price)
        data = await self._auth_post("/v2/orders", body)
        return data.get("result", {})

    async def cancel_order(self, order_id: int, product_id: int) -> dict:
        data = await self._auth_delete("/v2/orders", {
            "id": order_id,
            "product_id": product_id,
        })
        return data.get("result", {})

    async def close(self):
        await self.client.aclose()


delta_client = DeltaClient()
