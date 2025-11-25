"""BlackPanther - Exchange Manager (CCXT + Custom Futures Client)"""
import ccxt.async_support as ccxt
from loguru import logger
from config import settings
from typing import Optional, Dict, Any, List
import asyncio
from .binance_futures import BinanceFuturesTestnet


class ExchangeManager:
    """Unified exchange interface for Binance (Spot + Futures) and Gate.io"""
    
    def __init__(self):
        self.binance: Optional[ccxt.binance] = None  # Spot
        self.binance_futures: Optional[BinanceFuturesTestnet] = None  # Futures (custom)
        self.gate: Optional[ccxt.gateio] = None
        self._connected = False
        
    async def connect(self):
        """Initialize exchange connections"""
        try:
            # ============================================================
            # BINANCE CONFIGURATION
            # ============================================================
            # TESTNET mode: 
            #   - Spot testnet (testnet.binance.vision) for balance/orders
            #   - Production futures for market data (OI, funding, etc.)
            # LIVE mode: Production with full auth
            
            if settings.BINANCE_TESTNET:
                # Binance Spot Testnet (CCXT) - for spot orders
                self.binance = ccxt.binance({
                    'apiKey': settings.BINANCE_API_KEY,
                    'secret': settings.BINANCE_API_SECRET,
                    'enableRateLimit': True,
                    'sandbox': True,  # Uses testnet.binance.vision
                    'options': {
                        'defaultType': 'spot',
                        'adjustForTimeDifference': True
                    }
                })
                
                # Binance Futures Testnet (Custom Client) - for perp orders
                self.binance_futures = BinanceFuturesTestnet(
                    api_key=settings.BINANCE_FUTURES_API_KEY,
                    api_secret=settings.BINANCE_FUTURES_API_SECRET
                )
                await self.binance_futures.connect()
            else:
                # Production mode - use CCXT for both
                self.binance = ccxt.binance({
                    'apiKey': settings.BINANCE_API_KEY,
                    'secret': settings.BINANCE_API_SECRET,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',
                        'adjustForTimeDifference': True
                    }
                })
                self.binance_futures = None  # Use self.binance for futures in prod
            
            # ============================================================
            # GATE.IO CONFIGURATION
            # ============================================================
            # Use sandbox mode for testnet (50,633 USDT available!)
            gate_options = {
                'enableRateLimit': True,
                'sandbox': True,  # Gate.io testnet works with sandbox=True
            }
            if settings.GATEIO_API_KEY and settings.GATEIO_API_SECRET:
                gate_options['apiKey'] = settings.GATEIO_API_KEY
                gate_options['secret'] = settings.GATEIO_API_SECRET
            
            self.gate = ccxt.gateio(gate_options)
            
            # ============================================================
            # TEST CONNECTIONS
            # ============================================================
            await self.binance.load_markets()
            await self.gate.load_markets()
            
            self._connected = True
            logger.info("🐆 Exchange connections established")
            
            # Log balances (non-fatal if fails)
            try:
                spot_bal = await self.get_balance()
                logger.info(f"   Binance Spot: ${spot_bal['total']:,.2f} USDT")
            except Exception as e:
                logger.warning(f"   Binance Spot balance check failed: {e}")
            
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                try:
                    futures_bal = await self.binance_futures.get_balance()
                    logger.info(f"   Binance Futures: ${futures_bal['total']:,.2f} USDT")
                except Exception as e:
                    logger.warning(f"   Binance Futures balance check failed: {e}")
            
        except Exception as e:
            logger.error(f"Exchange connection failed: {e}")
            raise
    
    async def close(self):
        """Close all exchange connections"""
        if self.binance:
            await self.binance.close()
        if self.binance_futures:
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                await self.binance_futures.close()
            elif self.binance_futures != self.binance:
                await self.binance_futures.close()
        if self.gate:
            await self.gate.close()
        self._connected = False
        logger.info("Exchange connections closed")
    
    # === BINANCE FUTURES METHODS ===
    
    def _to_binance_symbol(self, symbol: str) -> str:
        """Convert CCXT symbol to Binance format: BTC/USDT:USDT -> BTCUSDT"""
        return symbol.replace("/", "").replace(":USDT", "")
    
    async def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate for a perpetual contract"""
        try:
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                return await self.binance_futures.get_funding_rate(self._to_binance_symbol(symbol))
            else:
                ticker = await self.binance.fetch_ticker(symbol)
                return float(ticker['info'].get('lastFundingRate', 0))
        except Exception as e:
            logger.error(f"Failed to get funding rate for {symbol}: {e}")
            return 0.0
    
    async def get_perp_price(self, symbol: str) -> float:
        """Get perpetual contract price"""
        if isinstance(self.binance_futures, BinanceFuturesTestnet):
            ticker = await self.binance_futures.get_ticker(self._to_binance_symbol(symbol))
            return ticker['price']
        else:
            ticker = await self.binance.fetch_ticker(symbol)
            return float(ticker['last'])
    
    async def get_spot_price(self, symbol: str) -> float:
        """Get spot price (remove :USDT suffix for spot)"""
        spot_symbol = symbol.replace(":USDT", "")
        ticker = await self.binance.fetch_ticker(spot_symbol)
        return float(ticker['last'])
    
    async def get_open_interest(self, symbol: str) -> float:
        """Get open interest for a futures symbol"""
        try:
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                return await self.binance_futures.get_open_interest(self._to_binance_symbol(symbol))
            else:
                oi = await self.binance.fetch_open_interest(symbol)
                return float(oi['openInterestAmount'])
        except Exception as e:
            logger.error(f"Failed to get OI for {symbol}: {e}")
            return 0.0
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> List:
        """Fetch OHLCV data from futures"""
        if isinstance(self.binance_futures, BinanceFuturesTestnet):
            return await self.binance_futures.get_klines(self._to_binance_symbol(symbol), timeframe, limit)
        else:
            return await self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    async def create_futures_order(
        self, 
        symbol: str, 
        side: str, 
        amount: float, 
        order_type: str = 'market',
        price: Optional[float] = None
    ) -> Dict:
        """Create order on Binance Futures"""
        try:
            binance_symbol = self._to_binance_symbol(symbol)
            
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                if order_type == 'market':
                    order = await self.binance_futures.create_market_order(binance_symbol, side, amount)
                else:
                    order = await self.binance_futures.create_limit_order(binance_symbol, side, amount, price)
            else:
                order = await self.binance.create_order(
                    symbol=symbol, type=order_type, side=side, amount=amount, price=price
                )
            
            logger.info(f"Futures order: {side} {amount} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Futures order failed: {e}")
            raise
    
    async def create_spot_order(
        self, 
        symbol: str, 
        side: str, 
        amount: float, 
        order_type: str = 'market',
        price: Optional[float] = None
    ) -> Dict:
        """Create order on Binance Spot"""
        try:
            order = await self.binance.create_order(
                symbol=symbol, type=order_type, side=side, amount=amount, price=price
            )
            logger.info(f"Spot order: {side} {amount} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Spot order failed: {e}")
            raise
    
    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a futures symbol"""
        try:
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                await self.binance_futures.set_leverage(self._to_binance_symbol(symbol), leverage)
            else:
                await self.binance.set_leverage(leverage, symbol)
        except Exception as e:
            logger.warning(f"Failed to set leverage: {e}")
    
    async def get_futures_positions(self) -> List[Dict]:
        """Get all open futures positions"""
        try:
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                return await self.binance_futures.get_positions()
            else:
                positions = await self.binance.fetch_positions()
                return [p for p in positions if float(p['contracts']) > 0]
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []
    
    async def close_futures_position(self, symbol: str):
        """Close a futures position"""
        if isinstance(self.binance_futures, BinanceFuturesTestnet):
            await self.binance_futures.close_position(self._to_binance_symbol(symbol))
        else:
            positions = await self.get_futures_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    side = 'sell' if pos['side'] == 'long' else 'buy'
                    await self.create_futures_order(symbol, side, abs(float(pos['contracts'])))
                    return
    
    async def cancel_all_futures_orders(self, symbol: Optional[str] = None):
        """Cancel all open futures orders"""
        try:
            if isinstance(self.binance_futures, BinanceFuturesTestnet):
                if symbol:
                    await self.binance_futures.cancel_all_orders(self._to_binance_symbol(symbol))
            else:
                if symbol:
                    await self.binance.cancel_all_orders(symbol)
            logger.info("All futures orders cancelled")
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
    
    async def get_balance(self) -> Dict:
        """Get spot account balance"""
        balance = await self.binance.fetch_balance()
        return {
            'total': float(balance['total'].get('USDT', 0)),
            'free': float(balance['free'].get('USDT', 0)),
            'used': float(balance['used'].get('USDT', 0))
        }
    
    async def get_futures_balance(self) -> Dict:
        """Get futures account balance"""
        if isinstance(self.binance_futures, BinanceFuturesTestnet):
            return await self.binance_futures.get_balance()
        else:
            balance = await self.binance.fetch_balance()
            return {
                'total': float(balance['total'].get('USDT', 0)),
                'free': float(balance['free'].get('USDT', 0)),
                'used': float(balance['used'].get('USDT', 0))
            }
    
    # === GATE.IO METHODS (for Sniper) ===
    
    # Known liquid pairs on Gate.io testnet (fallback whitelist)
    GATEIO_TESTNET_LIQUID_PAIRS = [
        'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'DOGE/USDT', 'SOL/USDT',
        'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT', 'LINK/USDT'
    ]
    
    async def gate_check_liquidity(
        self, 
        symbol: str, 
        min_orderbook_depth: float = 100.0,  # Min USDT value on each side
        max_spread_pct: float = 2.0  # Max bid-ask spread %
    ) -> Dict[str, Any]:
        """
        Check if a Gate.io pair has sufficient liquidity for trading.
        Returns: {tradeable: bool, reason: str, spread: float, bid_depth: float, ask_depth: float}
        """
        result = {
            'tradeable': False,
            'reason': '',
            'spread': 0.0,
            'bid_depth': 0.0,
            'ask_depth': 0.0,
            'symbol': symbol
        }
        
        try:
            # Fetch orderbook
            orderbook = await self.gate.fetch_order_book(symbol, limit=20)
            
            if not orderbook['bids'] or not orderbook['asks']:
                result['reason'] = 'Empty orderbook - no bids or asks'
                return result
            
            best_bid = orderbook['bids'][0][0]
            best_ask = orderbook['asks'][0][0]
            
            # Calculate spread
            spread_pct = ((best_ask - best_bid) / best_bid) * 100
            result['spread'] = spread_pct
            
            if spread_pct > max_spread_pct:
                result['reason'] = f'Spread too wide: {spread_pct:.2f}% > {max_spread_pct}%'
                return result
            
            # Calculate depth (USDT value in top 10 levels)
            bid_depth = sum(price * qty for price, qty in orderbook['bids'][:10])
            ask_depth = sum(price * qty for price, qty in orderbook['asks'][:10])
            result['bid_depth'] = bid_depth
            result['ask_depth'] = ask_depth
            
            if bid_depth < min_orderbook_depth:
                result['reason'] = f'Bid depth too low: ${bid_depth:.2f} < ${min_orderbook_depth}'
                return result
            
            if ask_depth < min_orderbook_depth:
                result['reason'] = f'Ask depth too low: ${ask_depth:.2f} < ${min_orderbook_depth}'
                return result
            
            # All checks passed
            result['tradeable'] = True
            result['reason'] = 'Liquidity OK'
            return result
            
        except Exception as e:
            result['reason'] = f'Liquidity check failed: {str(e)}'
            return result
    
    async def gate_get_tradeable_pairs(self, candidates: List[str] = None) -> List[str]:
        """
        Filter pairs to only those with sufficient liquidity.
        If candidates is None, uses the known liquid pairs whitelist.
        """
        if candidates is None:
            candidates = self.GATEIO_TESTNET_LIQUID_PAIRS
        
        tradeable = []
        for symbol in candidates:
            check = await self.gate_check_liquidity(symbol)
            if check['tradeable']:
                tradeable.append(symbol)
            else:
                logger.debug(f"Skipping {symbol}: {check['reason']}")
        
        return tradeable
    
    async def gate_fetch_tickers(self) -> Dict:
        """Fetch all Gate.io tickers"""
        return await self.gate.fetch_tickers()
    
    async def gate_fetch_ohlcv(self, symbol: str, timeframe: str = '1d', limit: int = 10) -> List:
        """Fetch Gate.io OHLCV for volume analysis"""
        return await self.gate.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    async def gate_buy_spot(self, symbol: str, amount: float, check_liquidity: bool = True) -> Dict:
        """
        Buy spot on Gate.io with optional liquidity check.
        Returns order dict or raises exception.
        """
        if check_liquidity:
            liquidity = await self.gate_check_liquidity(symbol)
            if not liquidity['tradeable']:
                raise Exception(f"Cannot trade {symbol}: {liquidity['reason']}")
        
        return await self.gate.create_order(
            symbol=symbol,
            type='market',
            side='buy',
            amount=amount
        )
    
    async def gate_sell_spot(self, symbol: str, amount: float, check_liquidity: bool = True) -> Dict:
        """
        Sell spot on Gate.io with optional liquidity check.
        Returns order dict or raises exception.
        """
        if check_liquidity:
            liquidity = await self.gate_check_liquidity(symbol)
            if not liquidity['tradeable']:
                raise Exception(f"Cannot trade {symbol}: {liquidity['reason']}")
        
        return await self.gate.create_order(
            symbol=symbol,
            type='market',
            side='sell',
            amount=amount
        )
    
    # === UTILITY METHODS ===
    
    async def ping(self) -> int:
        """Check exchange latency (ms)"""
        import time
        start = time.time()
        await self.binance.fetch_time()
        return int((time.time() - start) * 1000)

    # === BACKWARD COMPATIBILITY ===
    
    async def create_order(self, symbol: str, side: str, amount: float, 
                          order_type: str = 'market', price: Optional[float] = None,
                          params: Dict = None) -> Dict:
        """Backward compatible - routes to futures"""
        return await self.create_futures_order(symbol, side, amount, order_type, price)
    
    async def get_positions(self) -> List[Dict]:
        """Backward compatible - routes to futures"""
        return await self.get_futures_positions()
    
    async def close_position(self, symbol: str):
        """Backward compatible - routes to futures"""
        return await self.close_futures_position(symbol)
    
    async def cancel_all_orders(self, symbol: Optional[str] = None):
        """Backward compatible - routes to futures"""
        return await self.cancel_all_futures_orders(symbol)
