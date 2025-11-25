"""BlackPanther - Redis State Manager"""
import redis.asyncio as redis
from loguru import logger
from config import settings
from typing import Optional, Dict, Any
import json

class StateManager:
    """Redis-based state management for <1ms latency operations"""
    
    # Key prefixes
    PREFIX = "blackpanther"
    KILL_SWITCH = f"{PREFIX}:state:kill_switch"
    DAILY_PNL = f"{PREFIX}:risk:daily_pnl"
    START_EQUITY = f"{PREFIX}:risk:start_equity"
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("🔴 Redis connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    # === KILL SWITCH ===
    
    async def get_kill_switch(self) -> bool:
        """Check if kill switch is active"""
        val = await self.redis.get(self.KILL_SWITCH)
        return val == "true"
    
    async def set_kill_switch(self, active: bool):
        """Activate/deactivate kill switch"""
        await self.redis.set(self.KILL_SWITCH, "true" if active else "false")
        if active:
            logger.critical("🚨 KILL SWITCH ACTIVATED")
    
    # === POSITION TRACKING ===
    
    async def set_position(self, symbol: str, data: Dict):
        """Store position data"""
        key = f"{self.PREFIX}:pos:{symbol}"
        await self.redis.hset(key, mapping={
            'entry_price': str(data.get('entry_price', 0)),
            'size': str(data.get('size', 0)),
            'side': data.get('side', ''),
            'strategy': data.get('strategy', ''),
            'entry_time': data.get('entry_time', '')
        })
    
    async def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position data"""
        key = f"{self.PREFIX}:pos:{symbol}"
        data = await self.redis.hgetall(key)
        if data:
            return {
                'entry_price': float(data.get('entry_price', 0)),
                'size': float(data.get('size', 0)),
                'side': data.get('side', ''),
                'strategy': data.get('strategy', ''),
                'entry_time': data.get('entry_time', '')
            }
        return None
    
    async def delete_position(self, symbol: str):
        """Remove position from state"""
        key = f"{self.PREFIX}:pos:{symbol}"
        await self.redis.delete(key)
    
    async def get_all_positions(self) -> Dict[str, Dict]:
        """Get all tracked positions"""
        positions = {}
        async for key in self.redis.scan_iter(f"{self.PREFIX}:pos:*"):
            symbol = key.split(":")[-1]
            positions[symbol] = await self.get_position(symbol)
        return positions
    
    # === PNL TRACKING ===
    
    async def set_start_equity(self, equity: float):
        """Set starting equity for the day"""
        await self.redis.set(self.START_EQUITY, str(equity))
    
    async def get_start_equity(self) -> float:
        """Get starting equity"""
        val = await self.redis.get(self.START_EQUITY)
        return float(val) if val else 0.0
    
    async def update_daily_pnl(self, pnl: float):
        """Update daily PnL"""
        await self.redis.set(self.DAILY_PNL, str(pnl))
    
    async def get_daily_pnl(self) -> float:
        """Get current daily PnL"""
        val = await self.redis.get(self.DAILY_PNL)
        return float(val) if val else 0.0
    
    # === SIGNAL CACHING ===
    
    async def cache_signal(self, strategy: str, symbol: str, signal: Dict, ttl: int = 300):
        """Cache a signal for 5 minutes"""
        key = f"{self.PREFIX}:signal:{strategy}:{symbol}"
        await self.redis.setex(key, ttl, json.dumps(signal))
    
    async def get_cached_signal(self, strategy: str, symbol: str) -> Optional[Dict]:
        """Get cached signal"""
        key = f"{self.PREFIX}:signal:{strategy}:{symbol}"
        val = await self.redis.get(key)
        return json.loads(val) if val else None
    
    # === BASIS TRACKING (Cash Cow) ===
    
    async def set_basis(self, symbol: str, basis: float):
        """Store current basis spread"""
        key = f"{self.PREFIX}:basis:{symbol}"
        await self.redis.set(key, str(basis))
    
    async def get_basis(self, symbol: str) -> float:
        """Get stored basis spread"""
        key = f"{self.PREFIX}:basis:{symbol}"
        val = await self.redis.get(key)
        return float(val) if val else 0.0
    
    # === CVD TRACKING (Trend Killer) ===
    
    async def set_cvd(self, symbol: str, cvd: float):
        """Store CVD value"""
        key = f"{self.PREFIX}:cvd:{symbol}"
        await self.redis.set(key, str(cvd))
    
    async def get_cvd(self, symbol: str) -> float:
        """Get stored CVD"""
        key = f"{self.PREFIX}:cvd:{symbol}"
        val = await self.redis.get(key)
        return float(val) if val else 0.0
