"""
BlackPanther - Moonshot Sniper Strategy (Gate.io Listings)

Goal: Pre-position before Binance listing announcements
Allocation: 30% of Equity

The God Mode Enhancement: RVOL Pre-positioning
- RVOL > 5.0 (500% Volume Spike) AND Price_Change < 5%
- Meaning: Whales are accumulating silently without moving price
"""
import asyncio
from loguru import logger
from typing import Optional, Dict, List
from config import CONFIG
from intelligence.perplexity_client import PerplexityClient
from .base import BaseStrategy

class SniperStrategy(BaseStrategy):
    """Gate.io RVOL Scanner + Perplexity Sentiment for Listing Plays"""
    
    name = "SNIPER"
    allocation_pct = CONFIG["STRATEGIES"]["SNIPER"]["ALLOCATION_PCT"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = CONFIG["STRATEGIES"]["SNIPER"]
        self.rvol_threshold = self.config["RVOL_THRESHOLD"]
        self.price_change_max = self.config["PRICE_CHANGE_MAX"]
        self.sentiment_threshold = self.config["SENTIMENT_THRESHOLD"]
        self.trailing_stop_pct = self.config["TRAILING_STOP_PCT"]
        
        self.perplexity = PerplexityClient()
        
        # Track volume history for RVOL calculation
        self.volume_history: Dict[str, List[float]] = {}
        
        # Active sniper positions
        self.active_positions: Dict[str, Dict] = {}
        
        # Blacklist (already pumped or known scams)
        self.blacklist: set = set()
    
    async def run(self):
        """Main strategy loop"""
        while self.running:
            try:
                # 1. Monitor active positions for exit
                await self._monitor_positions()
                
                # 2. Scan for new opportunities
                if await self.is_safe_to_trade():
                    await self._scan_gate_anomalies()
                
                # Scan every 10 seconds (as per spec)
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Sniper error: {e}")
                await asyncio.sleep(5)
    
    async def _scan_gate_anomalies(self):
        """Scan Gate.io for volume anomalies"""
        try:
            tickers = await self.exchange.gate_fetch_tickers()
            
            for symbol, data in tickers.items():
                # Skip blacklisted
                if symbol in self.blacklist:
                    continue
                
                # Skip if already in position
                if symbol in self.active_positions:
                    continue
                
                # Filter: Mid-Cap only ($5M - $50M daily volume)
                quote_volume = data.get('quoteVolume', 0)
                if not (5_000_000 < quote_volume < 50_000_000):
                    continue
                
                # Check for anomaly
                signal = await self.get_signal(symbol)
                
                if signal and signal.get('action') == 'BUY_GATE':
                    await self._execute_sniper_buy(symbol, signal)
                    
        except Exception as e:
            logger.error(f"Gate.io scan failed: {e}")
    
    async def get_signal(self, symbol: str) -> Optional[Dict]:
        """
        Detect insider accumulation pattern:
        - RVOL > 5.0 (500% volume spike)
        - Price change < 5% (silent accumulation)
        - Perplexity sentiment > 70 (rumor validation)
        """
        try:
            # Get current ticker data
            tickers = await self.exchange.gate_fetch_tickers()
            data = tickers.get(symbol)
            
            if not data:
                return None
            
            # Calculate RVOL (Relative Volume)
            avg_vol = await self._get_10day_avg_volume(symbol)
            
            if avg_vol <= 0:
                return None
            
            current_vol = data.get('baseVolume', 0)
            rvol = current_vol / avg_vol
            
            # Get price change
            price_change = abs(data.get('percentage', 0)) / 100
            
            # === THE INSIDER LOADING PATTERN ===
            # Huge Volume (RVOL > 5) + Price NOT Moving (< 5% change)
            # This means someone is accumulating silently.
            
            if rvol > self.rvol_threshold and price_change < self.price_change_max:
                logger.info(
                    f"👀 INSIDER ACCUMULATION DETECTED on {symbol} | "
                    f"RVOL: {rvol:.1f}x | Price Change: {price_change*100:.1f}%"
                )
                
                # Verify with Perplexity (The final check)
                rumor_result = await self.perplexity.check_listing_rumors(symbol)
                rumor_score = rumor_result.get('score', 0)
                
                logger.info(f"Perplexity rumor score for {symbol}: {rumor_score}/100")
                
                if rumor_score >= self.sentiment_threshold:
                    return {
                        'action': 'BUY_GATE',
                        'symbol': symbol,
                        'rvol': rvol,
                        'price_change': price_change,
                        'rumor_score': rumor_score,
                        'rumor_summary': rumor_result.get('summary', ''),
                        'current_price': data.get('last', 0)
                    }
                else:
                    logger.info(f"Rumor score too low for {symbol}: {rumor_score}")
            
            return None
            
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return None
    
    async def _get_10day_avg_volume(self, symbol: str) -> float:
        """Get 10-day average volume for RVOL calculation"""
        try:
            # Check cache first
            if symbol in self.volume_history and len(self.volume_history[symbol]) >= 10:
                return sum(self.volume_history[symbol][-10:]) / 10
            
            # Fetch historical data
            ohlcv = await self.exchange.gate_fetch_ohlcv(symbol, '1d', limit=10)
            
            if not ohlcv or len(ohlcv) < 5:
                return 0
            
            volumes = [candle[5] for candle in ohlcv]  # Volume is index 5
            
            # Cache it
            self.volume_history[symbol] = volumes
            
            return sum(volumes) / len(volumes)
            
        except Exception as e:
            logger.error(f"Failed to get avg volume for {symbol}: {e}")
            return 0
    
    async def _execute_sniper_buy(self, symbol: str, signal: Dict):
        """Execute a sniper buy on Gate.io"""
        try:
            # === LIQUIDITY CHECK (Gate.io testnet has many illiquid pairs) ===
            liquidity = await self.exchange.gate_check_liquidity(symbol)
            if not liquidity['tradeable']:
                logger.warning(
                    f"⚠️ Skipping {symbol}: {liquidity['reason']} | "
                    f"Spread: {liquidity['spread']:.2f}% | "
                    f"Bid depth: ${liquidity['bid_depth']:.0f} | "
                    f"Ask depth: ${liquidity['ask_depth']:.0f}"
                )
                return
            
            # Calculate position size (max 5% of equity per moonshot)
            balance = await self.exchange.get_balance()
            max_allocation = balance['free'] * CONFIG["SYSTEM"].get("MAX_MOONSHOT_ALLOCATION_PCT", 0.05)
            
            current_price = signal['current_price']
            size = max_allocation / current_price
            
            if size <= 0:
                return
            
            logger.info(
                f"🎯 SNIPER BUY: {symbol} @ {current_price} | "
                f"Liquidity OK (spread: {liquidity['spread']:.2f}%)"
            )
            
            # Execute buy (skip liquidity check since we already did it)
            order = await self.exchange.gate_buy_spot(symbol, size, check_liquidity=False)
            
            # Track position
            self.active_positions[symbol] = {
                'entry_price': current_price,
                'size': size,
                'entry_time': str(__import__('datetime').datetime.utcnow()),
                'rvol': signal['rvol'],
                'rumor_score': signal['rumor_score'],
                'highest_price': current_price,
                'sold_50_pct': False
            }
            
            # Log entry
            await self.log_entry(
                symbol=symbol,
                side='buy',
                price=current_price,
                size=size,
                meta={
                    'rvol': f"{signal['rvol']:.1f}x",
                    'rumor_score': signal['rumor_score'],
                    'rumor_summary': signal['rumor_summary'][:100]
                }
            )
            
            logger.info(f"✅ Sniper position opened: {symbol}")
            
        except Exception as e:
            logger.error(f"Sniper buy failed for {symbol}: {e}")
    
    async def _monitor_positions(self):
        """Monitor active positions for exit conditions"""
        for symbol, pos in list(self.active_positions.items()):
            try:
                # Get current price
                tickers = await self.exchange.gate_fetch_tickers()
                data = tickers.get(symbol)
                
                if not data:
                    continue
                
                current_price = data.get('last', 0)
                entry_price = pos['entry_price']
                highest_price = pos['highest_price']
                
                # Update highest price
                if current_price > highest_price:
                    pos['highest_price'] = current_price
                    highest_price = current_price
                
                # Calculate PnL
                pnl_pct = ((current_price - entry_price) / entry_price)
                
                # === EXIT LOGIC ===
                
                # 1. Check for Binance listing announcement (manual trigger or API)
                # In production, you'd monitor Binance announcements API
                # For now, we use a profit target as proxy
                
                # 2. Sell 50% at 2x (100% gain)
                if pnl_pct >= 1.0 and not pos['sold_50_pct']:
                    await self._partial_exit(symbol, pos, 0.5, current_price, "100% GAIN")
                    pos['sold_50_pct'] = True
                    pos['size'] = pos['size'] * 0.5
                
                # 3. Trailing stop on remaining (-5% from high)
                if pos['sold_50_pct']:
                    drawdown_from_high = (highest_price - current_price) / highest_price
                    
                    if drawdown_from_high >= self.trailing_stop_pct:
                        await self._full_exit(symbol, pos, current_price, "TRAILING_STOP")
                        del self.active_positions[symbol]
                        continue
                
                # 4. Stop loss at -20% (cut losses)
                if pnl_pct <= -0.20:
                    await self._full_exit(symbol, pos, current_price, "STOP_LOSS")
                    del self.active_positions[symbol]
                    self.blacklist.add(symbol)  # Don't re-enter
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
    
    async def _partial_exit(self, symbol: str, pos: Dict, pct: float, price: float, reason: str):
        """Partial exit from position"""
        try:
            sell_size = pos['size'] * pct
            
            await self.exchange.gate_sell_spot(symbol, sell_size)
            
            pnl = (price - pos['entry_price']) * sell_size
            
            logger.info(f"💰 Partial exit {symbol}: {pct*100}% @ {price} | Reason: {reason}")
            
            if self.telegram:
                await self.telegram.send_trade_exit(
                    strategy=self.name,
                    symbol=symbol,
                    entry_price=pos['entry_price'],
                    exit_price=price,
                    pnl=pnl,
                    pnl_pct=((price - pos['entry_price']) / pos['entry_price']) * 100
                )
                
        except Exception as e:
            logger.error(f"Partial exit failed for {symbol}: {e}")
    
    async def _full_exit(self, symbol: str, pos: Dict, price: float, reason: str):
        """Full exit from position"""
        try:
            await self.exchange.gate_sell_spot(symbol, pos['size'])
            
            pnl = (price - pos['entry_price']) * pos['size']
            
            logger.info(f"🚪 Full exit {symbol} @ {price} | Reason: {reason}")
            
            await self.log_exit(
                symbol=symbol,
                exit_price=price,
                pnl=pnl
            )
            
        except Exception as e:
            logger.error(f"Full exit failed for {symbol}: {e}")
