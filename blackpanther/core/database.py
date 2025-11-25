"""BlackPanther - Supabase Database Manager"""
from supabase import create_client, Client
from loguru import logger
from config import settings
from typing import Optional, Dict, List
from datetime import datetime
import uuid

class DatabaseManager:
    """PostgreSQL via Supabase for trade journaling and analytics"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        
    async def connect(self):
        """Initialize Supabase client with service role key for RLS bypass"""
        try:
            # Use SERVICE_KEY to bypass RLS, fallback to regular key
            key = getattr(settings, 'SUPABASE_SERVICE_KEY', None) or settings.SUPABASE_KEY
            self.client = create_client(
                settings.SUPABASE_URL,
                key
            )
            logger.info("📊 Supabase connected")
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            raise
    
    async def log_trade(
        self,
        strategy: str,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: Optional[float] = None,
        pnl_usd: Optional[float] = None,
        meta_data: Optional[Dict] = None
    ):
        """Log a trade to the journal"""
        try:
            trade = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "strategy": strategy,
                "symbol": symbol,
                "side": side,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl_usd": pnl_usd,
                "meta_data": meta_data or {}
            }
            self.client.table("trade_journal").insert(trade).execute()
            logger.info(f"Trade logged: {strategy} {side} {symbol}")
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
    
    async def update_trade_exit(
        self,
        trade_id: str,
        exit_price: float,
        pnl_usd: float
    ):
        """Update trade with exit info"""
        try:
            self.client.table("trade_journal").update({
                "exit_price": exit_price,
                "pnl_usd": pnl_usd
            }).eq("id", trade_id).execute()
        except Exception as e:
            logger.error(f"Failed to update trade: {e}")
    
    async def get_daily_pnl(self) -> float:
        """Get total PnL for today"""
        try:
            today = datetime.utcnow().date().isoformat()
            result = self.client.table("trade_journal")\
                .select("pnl_usd")\
                .gte("timestamp", today)\
                .execute()
            
            total = sum(r['pnl_usd'] or 0 for r in result.data)
            return total
        except Exception as e:
            logger.error(f"Failed to get daily PnL: {e}")
            return 0.0
    
    async def get_strategy_stats(self, strategy: str, days: int = 30) -> Dict:
        """Get performance stats for a strategy"""
        try:
            from datetime import timedelta
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.client.table("trade_journal")\
                .select("*")\
                .eq("strategy", strategy)\
                .gte("timestamp", start_date)\
                .execute()
            
            trades = result.data
            if not trades:
                return {"total_trades": 0, "win_rate": 0, "total_pnl": 0}
            
            wins = [t for t in trades if (t['pnl_usd'] or 0) > 0]
            total_pnl = sum(t['pnl_usd'] or 0 for t in trades)
            
            return {
                "total_trades": len(trades),
                "win_rate": len(wins) / len(trades) * 100 if trades else 0,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(trades) if trades else 0
            }
        except Exception as e:
            logger.error(f"Failed to get strategy stats: {e}")
            return {}
    
    async def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Get recent trades"""
        try:
            result = self.client.table("trade_journal")\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            return []
