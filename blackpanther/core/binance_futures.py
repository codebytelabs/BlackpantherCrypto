"""
Binance Futures Testnet Client
Direct HTTP implementation since CCXT deprecated testnet support
"""
import httpx
import hmac
import hashlib
import time
from typing import Optional, Dict, List
from loguru import logger
from urllib.parse import urlencode


class BinanceFuturesTestnet:
    """Direct HTTP client for Binance Futures Testnet"""
    
    BASE_URL = "https://testnet.binancefuture.com"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client: Optional[httpx.AsyncClient] = None
        self.symbol_info: Dict[str, Dict] = {}  # Cache for symbol precision info
    
    async def connect(self):
        """Initialize HTTP client and load exchange info"""
        self.client = httpx.AsyncClient(timeout=30.0)
        await self._load_exchange_info()
        logger.info("🔥 Binance Futures Testnet connected")
    
    async def _load_exchange_info(self):
        """Load symbol precision info from exchange"""
        try:
            data = await self._get("/fapi/v1/exchangeInfo")
            for symbol in data.get("symbols", []):
                filters = {f["filterType"]: f for f in symbol.get("filters", [])}
                lot_size = filters.get("LOT_SIZE", {})
                min_notional = filters.get("MIN_NOTIONAL", {})
                
                self.symbol_info[symbol["symbol"]] = {
                    "stepSize": float(lot_size.get("stepSize", "0.001")),
                    "minQty": float(lot_size.get("minQty", "0.001")),
                    "maxQty": float(lot_size.get("maxQty", "1000")),
                    "minNotional": float(min_notional.get("notional", "100")),
                    "pricePrecision": symbol.get("pricePrecision", 2),
                    "quantityPrecision": symbol.get("quantityPrecision", 3)
                }
            logger.debug(f"Loaded info for {len(self.symbol_info)} symbols")
        except Exception as e:
            logger.warning(f"Failed to load exchange info: {e}")
    
    def _round_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to symbol's step size"""
        info = self.symbol_info.get(symbol, {})
        precision = info.get("quantityPrecision", 3)
        step_size = info.get("stepSize", 0.001)
        
        # Round to precision
        quantity = round(quantity, precision)
        
        # Ensure it's a multiple of step size
        if step_size > 0:
            quantity = round(quantity / step_size) * step_size
            quantity = round(quantity, precision)
        
        return quantity
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
    
    def _sign(self, params: dict) -> str:
        """Generate HMAC SHA256 signature"""
        query = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _headers(self) -> dict:
        """Get request headers"""
        return {"X-MBX-APIKEY": self.api_key}
    
    async def _get(self, endpoint: str, params: dict = None, signed: bool = False) -> dict:
        """Make GET request"""
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)
        
        url = f"{self.BASE_URL}{endpoint}"
        r = await self.client.get(url, params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()
    
    async def _post(self, endpoint: str, params: dict = None) -> dict:
        """Make signed POST request"""
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)
        
        url = f"{self.BASE_URL}{endpoint}"
        r = await self.client.post(url, params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()
    
    async def _delete(self, endpoint: str, params: dict = None) -> dict:
        """Make signed DELETE request"""
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)
        
        url = f"{self.BASE_URL}{endpoint}"
        r = await self.client.delete(url, params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()
    
    # === PUBLIC ENDPOINTS ===
    
    async def get_ticker(self, symbol: str) -> dict:
        """Get ticker price"""
        data = await self._get("/fapi/v1/ticker/price", {"symbol": symbol})
        return {"symbol": data["symbol"], "price": float(data["price"])}
    
    async def get_ticker_24h(self, symbol: str) -> dict:
        """Get 24h ticker stats"""
        return await self._get("/fapi/v1/ticker/24hr", {"symbol": symbol})
    
    async def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate"""
        data = await self._get("/fapi/v1/premiumIndex", {"symbol": symbol})
        return float(data.get("lastFundingRate", 0))
    
    async def get_klines(self, symbol: str, interval: str = "15m", limit: int = 100) -> List:
        """Get OHLCV data"""
        data = await self._get("/fapi/v1/klines", {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        })
        # Convert to CCXT format: [timestamp, open, high, low, close, volume]
        return [[
            int(k[0]),      # timestamp
            float(k[1]),    # open
            float(k[2]),    # high
            float(k[3]),    # low
            float(k[4]),    # close
            float(k[5])     # volume
        ] for k in data]
    
    async def get_open_interest(self, symbol: str) -> float:
        """Get open interest"""
        data = await self._get("/fapi/v1/openInterest", {"symbol": symbol})
        return float(data["openInterest"])
    
    # === PRIVATE ENDPOINTS ===
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        balances = await self._get("/fapi/v2/balance", signed=True)
        result = {"total": 0, "free": 0, "used": 0}
        for b in balances:
            if b["asset"] == "USDT":
                result["total"] = float(b["balance"])
                result["free"] = float(b["availableBalance"])
                result["used"] = result["total"] - result["free"]
                break
        return result
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        data = await self._get("/fapi/v2/positionRisk", signed=True)
        return [
            {
                "symbol": p["symbol"],
                "side": "long" if float(p["positionAmt"]) > 0 else "short",
                "contracts": abs(float(p["positionAmt"])),
                "entryPrice": float(p["entryPrice"]),
                "unrealizedPnl": float(p["unRealizedProfit"]),
                "leverage": int(p["leverage"])
            }
            for p in data if float(p["positionAmt"]) != 0
        ]
    
    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol"""
        await self._post("/fapi/v1/leverage", {
            "symbol": symbol,
            "leverage": leverage
        })
        logger.info(f"Leverage set to {leverage}x for {symbol}")
    
    async def create_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        """Create market order with proper quantity formatting"""
        # Round quantity to symbol's precision
        quantity = self._round_quantity(symbol, quantity)
        
        # Get symbol info for validation
        info = self.symbol_info.get(symbol, {})
        min_notional = info.get("minNotional", 100)
        min_qty = info.get("minQty", 0.001)
        
        # Validate minimum quantity
        if quantity < min_qty:
            raise ValueError(f"Quantity {quantity} below minimum {min_qty}")
        
        # Validate minimum notional
        ticker = await self.get_ticker(symbol)
        notional = quantity * ticker['price']
        
        if notional < min_notional:
            raise ValueError(f"Order notional ${notional:.2f} below minimum ${min_notional}")
        
        order = await self._post("/fapi/v1/order", {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity
        })
        logger.info(f"Market order: {side} {quantity} {symbol}")
        return order
    
    async def create_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        """Create limit order with proper precision"""
        # Round quantity and price to symbol's precision
        quantity = self._round_quantity(symbol, quantity)
        info = self.symbol_info.get(symbol, {})
        price_precision = info.get("pricePrecision", 2)
        price = round(price, price_precision)
        
        order = await self._post("/fapi/v1/order", {
            "symbol": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": quantity,
            "price": price
        })
        logger.info(f"Limit order: {side} {quantity} {symbol} @ {price}")
        return order
    
    async def cancel_order(self, symbol: str, order_id: int):
        """Cancel an order"""
        return await self._delete("/fapi/v1/order", {
            "symbol": symbol,
            "orderId": order_id
        })
    
    async def cancel_all_orders(self, symbol: str):
        """Cancel all open orders for a symbol"""
        return await self._delete("/fapi/v1/allOpenOrders", {"symbol": symbol})
    
    async def close_position(self, symbol: str):
        """Close a position"""
        positions = await self.get_positions()
        for pos in positions:
            if pos["symbol"] == symbol and pos["contracts"] > 0:
                side = "SELL" if pos["side"] == "long" else "BUY"
                await self.create_market_order(symbol, side, pos["contracts"])
                logger.info(f"Position closed: {symbol}")
                return
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol precision and limits info"""
        return self.symbol_info.get(symbol, {
            "stepSize": 0.001,
            "minQty": 0.001,
            "maxQty": 1000,
            "minNotional": 100,
            "pricePrecision": 2,
            "quantityPrecision": 3
        })
