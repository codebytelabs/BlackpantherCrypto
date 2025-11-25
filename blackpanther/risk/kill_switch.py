"""BlackPanther - Kill Switch (Risk Management Override)"""
import asyncio
from loguru import logger
from config import CONFIG, settings
from core.exchange import ExchangeManager
from core.state_manager import StateManager
from alerts.telegram import TelegramAlert
from typing import Optional

class KillSwitch:
    """
    Global risk management module that overrides all strategies.
    Runs on a separate monitoring loop.
    """
    
    def __init__(
        self,
        exchange: ExchangeManager,
        state: StateManager,
        telegram: Optional['TelegramAlert'] = None
    ):
        self.exchange = exchange
        self.state = state
        self.telegram = telegram
        self.running = False
        self.max_drawdown = CONFIG["SYSTEM"]["MAX_DAILY_DRAWDOWN_PCT"]
        self.max_latency_ms = 500
        
    async def start(self):
        """Start the kill switch monitoring loop"""
        self.running = True
        logger.info("🛡️ Kill Switch monitoring started")
        
        # Set starting equity
        balance = await self.exchange.get_balance()
        await self.state.set_start_equity(balance['total'])
        
        while self.running:
            try:
                await self._check_all_conditions()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Kill switch error: {e}")
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the monitoring loop"""
        self.running = False
    
    async def _check_all_conditions(self):
        """Run all risk checks"""
        # Skip if already triggered
        if await self.state.get_kill_switch():
            return
        
        # 1. Drawdown Check
        await self._check_drawdown()
        
        # 2. Latency Check
        await self._check_latency()
    
    async def _check_drawdown(self):
        """Check if daily drawdown exceeds limit"""
        try:
            balance = await self.exchange.get_balance()
            current_equity = balance['total']
            start_equity = await self.state.get_start_equity()
            
            if start_equity <= 0:
                return
            
            drawdown = (current_equity - start_equity) / start_equity
            
            # Update daily PnL in state
            await self.state.update_daily_pnl(current_equity - start_equity)
            
            if drawdown < -self.max_drawdown:
                await self._trigger_shutdown(
                    f"DRAWDOWN LIMIT HIT: {drawdown*100:.2f}%"
                )
        except Exception as e:
            logger.error(f"Drawdown check failed: {e}")
    
    async def _check_latency(self):
        """Check exchange API latency"""
        try:
            latency = await self.exchange.ping()
            
            if latency > self.max_latency_ms:
                logger.warning(f"⚠️ High latency detected: {latency}ms")
                # Don't shutdown, just pause new entries
                # This is handled by strategies checking latency
        except Exception as e:
            logger.error(f"Latency check failed: {e}")
    
    async def _trigger_shutdown(self, reason: str):
        """Execute emergency shutdown"""
        logger.critical(f"🚨 KILL SWITCH TRIGGERED: {reason}")
        
        # 1. Set kill switch flag
        await self.state.set_kill_switch(True)
        
        # 2. Cancel all orders
        try:
            await self.exchange.cancel_all_orders()
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
        
        # 3. Close all positions
        try:
            positions = await self.exchange.get_positions()
            for pos in positions:
                await self.exchange.close_position(pos['symbol'])
        except Exception as e:
            logger.error(f"Failed to close positions: {e}")
        
        # 4. Send alert
        if self.telegram:
            await self.telegram.send_critical(
                f"🚨 PROTOCOL SHUTDOWN\n\n"
                f"Reason: {reason}\n"
                f"All positions closed.\n"
                f"All orders cancelled.\n\n"
                f"Manual intervention required."
            )
        
        logger.critical("🛑 BLACKPANTHER SHUTDOWN COMPLETE")
    
    async def manual_shutdown(self, reason: str = "Manual trigger"):
        """Manually trigger shutdown"""
        await self._trigger_shutdown(reason)
    
    async def check_basis_risk(self, symbol: str, current_basis: float) -> bool:
        """
        Check if basis spread is within safe limits.
        Called by Cash Cow strategy.
        Returns True if safe, False if emergency close needed.
        """
        max_basis = CONFIG["STRATEGIES"]["CASH_COW"]["MAX_BASIS_RISK"]
        
        if abs(current_basis) > max_basis:
            logger.warning(
                f"🚨 BASIS BLOWOUT on {symbol}: {current_basis*100:.3f}%"
            )
            return False
        
        return True
    
    async def is_safe_to_trade(self) -> bool:
        """Check if it's safe to open new positions"""
        # Check kill switch
        if await self.state.get_kill_switch():
            return False
        
        # Check latency
        try:
            latency = await self.exchange.ping()
            if latency > self.max_latency_ms:
                logger.warning(f"Trading paused: High latency ({latency}ms)")
                return False
        except:
            return False
        
        return True
