"""
BlackPanther - Trend Killer Strategy (OI + SuperTrend + CVD)

Goal: Catch institutional moves; ignore retail noise
Allocation: 30% of Equity
Timeframe: 15m

The God Mode Enhancement: CVD Validation
- If Price UP + OI UP but CVD Flat/Down = FAKE PUMP (Reject)
- If Price UP + OI UP + CVD UP = GOD CANDLE (Send it)
"""
import asyncio
import pandas as pd
from loguru import logger
from typing import Optional, Dict, List
from config import CONFIG
from utils.indicators import supertrend as calc_supertrend, calculate_cvd
from .base import BaseStrategy

class TrendKillerStrategy(BaseStrategy):
    """OI + SuperTrend + CVD Trend Following"""
    
    name = "TREND_KILLER"
    allocation_pct = CONFIG["STRATEGIES"]["TREND_KILLER"]["ALLOCATION_PCT"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = CONFIG["STRATEGIES"]["TREND_KILLER"]
        self.timeframe = self.config["TIMEFRAME"]
        self.supertrend_length = self.config["SUPERTREND_LENGTH"]
        self.supertrend_mult = self.config["SUPERTREND_MULT"]
        self.oi_surge_threshold = self.config["OI_SURGE_THRESHOLD"]
        self.cvd_required = self.config["CVD_CONFIRMATION_REQUIRED"]
        
        self.watchlist = [
            "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT",
            "DOGE/USDT:USDT", "XRP/USDT:USDT", "AVAX/USDT:USDT",
            "LINK/USDT:USDT", "ARB/USDT:USDT"
        ]
        
        # Track OI history for surge detection
        self.oi_history: Dict[str, List[float]] = {}
    
    async def run(self):
        """Main strategy loop"""
        while self.running:
            try:
                if await self.is_safe_to_trade():
                    await self._scan_all_symbols()
                
                # Run every 5 minutes (aligned with 15m candles)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Trend Killer error: {e}")
                await asyncio.sleep(10)
    
    async def _scan_all_symbols(self):
        """Scan all symbols for signals"""
        for symbol in self.watchlist:
            try:
                signal = await self.get_signal(symbol)
                
                if signal and signal.get('signal') in ['LONG_FULL_SEND', 'SHORT_FULL_SEND']:
                    await self._execute_signal(symbol, signal)
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
    
    async def get_signal(self, symbol: str) -> Optional[Dict]:
        """
        Generate trading signal using Triple-Filter Validation:
        1. SuperTrend (Direction)
        2. Open Interest (Momentum)
        3. CVD (Truth - The Lie Detector)
        """
        try:
            # Fetch OHLCV data
            ohlcv = await self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate SuperTrend
            df = self._calculate_supertrend(df)
            
            # Calculate CVD
            df = self._calculate_cvd(df)
            
            # Get current OI
            current_oi = await self.exchange.get_open_interest(symbol)
            
            # Track OI history
            if symbol not in self.oi_history:
                self.oi_history[symbol] = []
            self.oi_history[symbol].append(current_oi)
            
            # Keep only last 4 readings (1 hour of 15m data)
            if len(self.oi_history[symbol]) > 4:
                self.oi_history[symbol] = self.oi_history[symbol][-4:]
            
            # Need at least 2 readings for comparison
            if len(self.oi_history[symbol]) < 2:
                return None
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            oi_1h_ago = self.oi_history[symbol][0]
            
            # === FILTER 1: SuperTrend Direction ===
            is_uptrend = latest['close'] > latest['supertrend']
            is_downtrend = latest['close'] < latest['supertrend']
            
            # === FILTER 2: OI Surge (>5% in 1 hour) ===
            oi_surge = current_oi > (oi_1h_ago * self.oi_surge_threshold)
            oi_change_pct = ((current_oi - oi_1h_ago) / oi_1h_ago) * 100 if oi_1h_ago > 0 else 0
            
            # === FILTER 3: CVD Confirmation (The Lie Detector) ===
            cvd_rising = latest['cvd'] > prev['cvd']
            cvd_falling = latest['cvd'] < prev['cvd']
            cvd_change = latest['cvd'] - prev['cvd']
            
            # Store CVD in state for monitoring
            await self.state.set_cvd(symbol, latest['cvd'])
            
            # === SIGNAL LOGIC ===
            
            # LONG Signal
            if is_uptrend and oi_surge:
                if self.cvd_required and not cvd_rising:
                    # FAKE PUMP DETECTED
                    logger.warning(
                        f"🚫 FAKE PUMP on {symbol}: "
                        f"Price UP + OI UP (+{oi_change_pct:.1f}%) but CVD FLAT/DOWN"
                    )
                    return {
                        'signal': 'REJECT',
                        'reason': 'CVD_DIVERGENCE',
                        'details': {
                            'oi_change': f"+{oi_change_pct:.1f}%",
                            'cvd_change': cvd_change
                        }
                    }
                
                # GOD CANDLE - All filters aligned
                logger.info(
                    f"🔥 GOD CANDLE on {symbol}: "
                    f"SuperTrend UP + OI +{oi_change_pct:.1f}% + CVD Rising"
                )
                
                return {
                    'signal': 'LONG_FULL_SEND',
                    'confidence': 'HIGH',
                    'entry_price': latest['close'],
                    'stop_loss': latest['supertrend'],
                    'details': {
                        'supertrend': latest['supertrend'],
                        'oi_change': f"+{oi_change_pct:.1f}%",
                        'cvd_rising': True
                    }
                }
            
            # SHORT Signal (inverse logic)
            if is_downtrend and oi_surge:
                if self.cvd_required and not cvd_falling:
                    logger.warning(
                        f"🚫 FAKE DUMP on {symbol}: "
                        f"Price DOWN + OI UP but CVD not falling"
                    )
                    return {
                        'signal': 'REJECT',
                        'reason': 'CVD_DIVERGENCE'
                    }
                
                logger.info(
                    f"🔥 SHORT SIGNAL on {symbol}: "
                    f"SuperTrend DOWN + OI +{oi_change_pct:.1f}% + CVD Falling"
                )
                
                return {
                    'signal': 'SHORT_FULL_SEND',
                    'confidence': 'HIGH',
                    'entry_price': latest['close'],
                    'stop_loss': latest['supertrend'],
                    'details': {
                        'supertrend': latest['supertrend'],
                        'oi_change': f"+{oi_change_pct:.1f}%",
                        'cvd_falling': True
                    }
                }
            
            return {'signal': 'WAIT'}
            
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return None
    
    def _calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate SuperTrend indicator using custom implementation"""
        try:
            st_result = calc_supertrend(
                df['high'], 
                df['low'], 
                df['close'],
                length=self.supertrend_length,
                multiplier=self.supertrend_mult
            )
            
            df['supertrend'] = st_result[f'SUPERT_{self.supertrend_length}_{self.supertrend_mult}']
            df['supertrend_direction'] = st_result[f'SUPERTd_{self.supertrend_length}_{self.supertrend_mult}']
            
        except Exception as e:
            logger.error(f"SuperTrend calculation failed: {e}")
            df['supertrend'] = df['close']
            df['supertrend_direction'] = 1
        
        return df
    
    def _calculate_cvd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Cumulative Volume Delta using custom implementation"""
        return calculate_cvd(df)
    
    async def _execute_signal(self, symbol: str, signal: Dict):
        """Execute a trading signal"""
        try:
            # Check if we already have a position
            existing = await self.state.get_position(symbol)
            if existing:
                logger.debug(f"Already have position in {symbol}")
                return
            
            side = 'buy' if signal['signal'] == 'LONG_FULL_SEND' else 'sell'
            
            # Calculate position size
            size = await self.get_position_size(symbol, side)
            
            if size <= 0:
                return
            
            # Set leverage
            leverage = min(10, CONFIG["SYSTEM"]["LEVERAGE_LIMIT"])
            await self.exchange.set_leverage(symbol, leverage)
            
            # Execute order
            order = await self.exchange.create_order(
                symbol=symbol,
                side=side,
                amount=size,
                order_type='market'
            )
            
            # Log entry
            await self.log_entry(
                symbol=symbol,
                side=side,
                price=signal['entry_price'],
                size=size,
                meta={
                    'confidence': signal['confidence'],
                    'stop_loss': signal['stop_loss'],
                    **signal.get('details', {})
                }
            )
            
            # Send signal alert
            if self.telegram:
                await self.telegram.send_signal(
                    strategy=self.name,
                    symbol=symbol,
                    signal_type=signal['signal'],
                    confidence=signal['confidence'],
                    details=signal.get('details', {})
                )
            
            logger.info(f"✅ {signal['signal']} executed: {symbol} @ {signal['entry_price']}")
            
        except Exception as e:
            logger.error(f"Failed to execute signal on {symbol}: {e}")
