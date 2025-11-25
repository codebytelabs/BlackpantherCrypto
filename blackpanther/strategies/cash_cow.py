"""
BlackPanther - Cash Cow Strategy (Funding Rate Arbitrage)

Goal: Risk-free yield capture (Target: 15-30% APY)
Allocation: 40% of Equity

The God Mode Enhancement: Basis Risk Monitor
- If abs(Basis) > 1%, IMMEDIATE FORCE CLOSE
"""
import asyncio
from loguru import logger
from typing import Optional, Dict, List
from config import CONFIG
from .base import BaseStrategy

class CashCowStrategy(BaseStrategy):
    """Delta-Neutral Funding Rate Arbitrage with Basis Protection"""
    
    name = "CASH_COW"
    allocation_pct = CONFIG["STRATEGIES"]["CASH_COW"]["ALLOCATION_PCT"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = CONFIG["STRATEGIES"]["CASH_COW"]
        self.min_funding_rate = self.config["MIN_FUNDING_RATE"]
        self.max_basis_risk = self.config["MAX_BASIS_RISK"]
        self.active_hedges: Dict[str, Dict] = {}  # symbol -> hedge info
        self.watchlist = [
            "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT",
            "DOGE/USDT:USDT", "XRP/USDT:USDT"
        ]
    
    async def run(self):
        """Main strategy loop"""
        while self.running:
            try:
                # 1. Monitor existing hedges for basis risk
                await self._monitor_active_hedges()
                
                # 2. Scan for new opportunities
                if await self.is_safe_to_trade():
                    await self._scan_opportunities()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Cash Cow error: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_active_hedges(self):
        """Monitor basis risk on all active hedges"""
        for symbol, hedge in list(self.active_hedges.items()):
            try:
                status = await self.monitor_risk(symbol)
                
                if status == "CLOSED":
                    del self.active_hedges[symbol]
                    logger.info(f"Hedge closed for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
    
    async def _scan_opportunities(self):
        """Scan for high funding rate opportunities"""
        for symbol in self.watchlist:
            # Skip if already hedged
            if symbol in self.active_hedges:
                continue
            
            try:
                signal = await self.get_signal(symbol)
                
                if signal and signal.get('action') == 'OPEN_HEDGE':
                    await self._open_hedge(symbol, signal)
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
    
    async def get_signal(self, symbol: str) -> Optional[Dict]:
        """Check if symbol is suitable for funding arb"""
        try:
            # Get funding rate
            funding_rate = await self.exchange.get_funding_rate(symbol)
            
            # Check minimum threshold
            if funding_rate < self.min_funding_rate:
                return None
            
            # Check current basis
            perp_price = await self.exchange.get_perp_price(symbol)
            spot_price = await self.exchange.get_spot_price(symbol)
            current_basis = (perp_price - spot_price) / spot_price
            
            # Reject if basis already too wide
            if abs(current_basis) > self.max_basis_risk * 0.5:
                logger.debug(f"{symbol} basis too wide for entry: {current_basis*100:.3f}%")
                return None
            
            # Calculate expected APY
            # Funding paid every 8h = 3x per day = 1095x per year
            expected_apy = funding_rate * 3 * 365 * 100
            
            return {
                'action': 'OPEN_HEDGE',
                'symbol': symbol,
                'funding_rate': funding_rate,
                'current_basis': current_basis,
                'expected_apy': expected_apy,
                'perp_price': perp_price,
                'spot_price': spot_price
            }
            
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return None
    
    async def _open_hedge(self, symbol: str, signal: Dict):
        """Open a delta-neutral hedge position"""
        try:
            # Calculate position size
            size = await self.get_position_size(symbol, 'hedge')
            
            if size <= 0:
                return
            
            logger.info(f"Opening hedge on {symbol} | Funding: {signal['funding_rate']*100:.4f}%")
            
            # CRITICAL: Execute both legs simultaneously
            # Short Perp + Long Spot
            perp_order, spot_order = await asyncio.gather(
                self.exchange.create_order(
                    symbol=symbol,
                    side='sell',
                    amount=size,
                    order_type='market'
                ),
                self._buy_spot_equivalent(symbol, size),
                return_exceptions=True
            )
            
            # Check for errors
            if isinstance(perp_order, Exception):
                logger.error(f"Perp order failed: {perp_order}")
                return
            
            if isinstance(spot_order, Exception):
                # Perp succeeded but spot failed - close perp immediately
                logger.error(f"Spot order failed, closing perp: {spot_order}")
                await self.exchange.close_position(symbol)
                return
            
            # Store hedge info
            self.active_hedges[symbol] = {
                'entry_time': str(__import__('datetime').datetime.utcnow()),
                'entry_basis': signal['current_basis'],
                'funding_rate': signal['funding_rate'],
                'perp_size': size,
                'spot_size': size,
                'perp_entry': signal['perp_price'],
                'spot_entry': signal['spot_price']
            }
            
            # Log entry
            await self.log_entry(
                symbol=symbol,
                side='hedge',
                price=signal['perp_price'],
                size=size,
                meta={
                    'funding_rate': f"{signal['funding_rate']*100:.4f}%",
                    'entry_basis': f"{signal['current_basis']*100:.4f}%",
                    'expected_apy': f"{signal['expected_apy']:.1f}%"
                }
            )
            
            logger.info(f"✅ Hedge opened: {symbol} | Size: {size}")
            
        except Exception as e:
            logger.error(f"Failed to open hedge on {symbol}: {e}")
    
    async def _buy_spot_equivalent(self, symbol: str, size: float):
        """Buy spot equivalent (simplified - in production use spot exchange)"""
        # For now, we'll use Binance spot
        spot_symbol = symbol.replace(":USDT", "")
        return await self.exchange.create_order(
            symbol=spot_symbol,
            side='buy',
            amount=size,
            order_type='market',
            params={'type': 'spot'}
        )
    
    async def monitor_risk(self, symbol: str) -> str:
        """
        Monitor basis risk for an active hedge.
        THE GOD MODE ENHANCEMENT.
        """
        try:
            # Get live prices
            perp_price = await self.exchange.get_perp_price(symbol)
            spot_price = await self.exchange.get_spot_price(symbol)
            
            # Calculate current basis spread
            current_spread = (perp_price - spot_price) / spot_price
            
            # Store in state for monitoring
            await self.state.set_basis(symbol, current_spread)
            
            # THE "OH SH*T" MONITOR
            # If the premium explodes > 1%, CLOSE. Don't wait. Save capital.
            if abs(current_spread) > self.max_basis_risk:
                logger.critical(
                    f"🚨 BASIS BLOWOUT ON {symbol}. "
                    f"SPREAD: {current_spread*100:.3f}%. EMERGENCY CLOSE."
                )
                
                await self._close_hedge(symbol, reason="BASIS_BLOWOUT")
                
                if self.telegram:
                    await self.telegram.send_critical(
                        f"🚨 BASIS BLOWOUT\n\n"
                        f"Symbol: {symbol}\n"
                        f"Spread: {current_spread*100:.3f}%\n"
                        f"Limit: {self.max_basis_risk*100:.1f}%\n\n"
                        f"Hedge closed to preserve capital."
                    )
                
                return "CLOSED"
            
            # Check if funding rate is still profitable
            funding_rate = await self.exchange.get_funding_rate(symbol)
            
            if funding_rate < self.min_funding_rate * 0.5:
                logger.info(f"Funding rate dropped on {symbol}: {funding_rate*100:.4f}%")
                # Don't close immediately, but flag for review
            
            return "MAINTAIN"
            
        except Exception as e:
            logger.error(f"Risk monitoring failed for {symbol}: {e}")
            return "ERROR"
    
    async def _close_hedge(self, symbol: str, reason: str = "NORMAL"):
        """Close a hedge position"""
        try:
            hedge = self.active_hedges.get(symbol)
            if not hedge:
                return
            
            logger.info(f"Closing hedge on {symbol} | Reason: {reason}")
            
            # Close both legs simultaneously
            await asyncio.gather(
                self.exchange.close_position(symbol),
                self._sell_spot_equivalent(symbol, hedge['spot_size']),
                return_exceptions=True
            )
            
            # Calculate PnL (simplified)
            perp_price = await self.exchange.get_perp_price(symbol)
            perp_pnl = (hedge['perp_entry'] - perp_price) * hedge['perp_size']
            
            await self.log_exit(
                symbol=symbol,
                exit_price=perp_price,
                pnl=perp_pnl
            )
            
            logger.info(f"✅ Hedge closed: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to close hedge on {symbol}: {e}")
    
    async def _sell_spot_equivalent(self, symbol: str, size: float):
        """Sell spot equivalent"""
        spot_symbol = symbol.replace(":USDT", "")
        return await self.exchange.create_order(
            symbol=spot_symbol,
            side='sell',
            amount=size,
            order_type='market',
            params={'type': 'spot'}
        )
