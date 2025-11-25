"""BlackPanther - Telegram Alert System"""
import httpx
from loguru import logger
from config import settings
from typing import Optional

class TelegramAlert:
    """Telegram bot for real-time alerts"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = bool(self.token and self.chat_id)
        
    async def send(self, message: str, parse_mode: str = "HTML"):
        """Send a message to Telegram"""
        if not self.enabled:
            logger.debug(f"Telegram disabled. Message: {message}")
            return
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": parse_mode
                    }
                )
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
    
    async def send_trade_entry(
        self,
        strategy: str,
        symbol: str,
        side: str,
        price: float,
        size: float,
        meta: Optional[dict] = None
    ):
        """Send trade entry notification"""
        emoji = "🟢" if side.upper() == "BUY" else "🔴"
        
        msg = (
            f"{emoji} <b>TRADE ENTRY</b>\n\n"
            f"Strategy: <code>{strategy}</code>\n"
            f"Symbol: <code>{symbol}</code>\n"
            f"Side: <code>{side.upper()}</code>\n"
            f"Price: <code>${price:,.2f}</code>\n"
            f"Size: <code>{size}</code>\n"
        )
        
        if meta:
            msg += "\n<b>Signals:</b>\n"
            for k, v in meta.items():
                msg += f"• {k}: <code>{v}</code>\n"
        
        await self.send(msg)
    
    async def send_trade_exit(
        self,
        strategy: str,
        symbol: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_pct: float
    ):
        """Send trade exit notification"""
        emoji = "💰" if pnl > 0 else "💸"
        color = "🟢" if pnl > 0 else "🔴"
        
        msg = (
            f"{emoji} <b>TRADE EXIT</b>\n\n"
            f"Strategy: <code>{strategy}</code>\n"
            f"Symbol: <code>{symbol}</code>\n"
            f"Entry: <code>${entry_price:,.2f}</code>\n"
            f"Exit: <code>${exit_price:,.2f}</code>\n"
            f"PnL: {color} <code>${pnl:,.2f} ({pnl_pct:+.2f}%)</code>\n"
        )
        
        await self.send(msg)
    
    async def send_signal(
        self,
        strategy: str,
        symbol: str,
        signal_type: str,
        confidence: str,
        details: dict
    ):
        """Send signal detection notification"""
        msg = (
            f"📡 <b>SIGNAL DETECTED</b>\n\n"
            f"Strategy: <code>{strategy}</code>\n"
            f"Symbol: <code>{symbol}</code>\n"
            f"Signal: <code>{signal_type}</code>\n"
            f"Confidence: <code>{confidence}</code>\n"
        )
        
        if details:
            msg += "\n<b>Details:</b>\n"
            for k, v in details.items():
                msg += f"• {k}: <code>{v}</code>\n"
        
        await self.send(msg)
    
    async def send_warning(self, message: str):
        """Send warning notification"""
        await self.send(f"⚠️ <b>WARNING</b>\n\n{message}")
    
    async def send_critical(self, message: str):
        """Send critical alert"""
        await self.send(f"🚨 <b>CRITICAL ALERT</b>\n\n{message}")
    
    async def send_daily_summary(
        self,
        total_pnl: float,
        trades_count: int,
        win_rate: float,
        best_trade: Optional[dict] = None,
        worst_trade: Optional[dict] = None
    ):
        """Send daily performance summary"""
        emoji = "📈" if total_pnl > 0 else "📉"
        
        msg = (
            f"{emoji} <b>DAILY SUMMARY</b>\n\n"
            f"Total PnL: <code>${total_pnl:,.2f}</code>\n"
            f"Trades: <code>{trades_count}</code>\n"
            f"Win Rate: <code>{win_rate:.1f}%</code>\n"
        )
        
        if best_trade:
            msg += f"\n🏆 Best: <code>{best_trade['symbol']}</code> +${best_trade['pnl']:,.2f}\n"
        
        if worst_trade:
            msg += f"💀 Worst: <code>{worst_trade['symbol']}</code> ${worst_trade['pnl']:,.2f}\n"
        
        await self.send(msg)
    
    async def send_startup(self, mode: str, strategies: list):
        """Send startup notification"""
        msg = (
            f"🐆 <b>BLACKPANTHER ONLINE</b>\n\n"
            f"Mode: <code>{mode}</code>\n"
            f"Strategies: <code>{', '.join(strategies)}</code>\n\n"
            f"<i>God Mode Activated</i>"
        )
        await self.send(msg)
