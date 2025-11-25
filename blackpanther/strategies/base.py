"""BlackPanther - Base Strategy Class"""
from abc import ABC, abstractmethod
from loguru import logger
from core.exchange import ExchangeManager
from core.state_manager import StateManager
from core.database import DatabaseManager
from alerts.telegram import TelegramAlert
from risk.kill_switch import KillSwitch
from typing import Optional, Dict, Any

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    name: str = "BaseStrategy"
    allocation_pct: float = 0.0
    
    def __init__(
        self,
        exchange: ExchangeManager,
        state: StateManager,
        database: DatabaseManager,
        telegram: Optional[TelegramAlert] = None,
        kill_switch: Optional[KillSwitch] = None
    ):
        self.exchange = exchange
        self.state = state
        self.database = database
        self.telegram = telegram
        self.kill_switch = kill_switch
        self.running = False
        
    @abstractmethod
    async def run(self):
        """Main strategy loop"""
        pass
    
    @abstractmethod
    async def get_signal(self, symbol: str) -> Optional[Dict]:
        """Generate trading signal for a symbol"""
        pass
    
    async def start(self):
        """Start the strategy"""
        self.running = True
        logger.info(f"🚀 {self.name} started")
        await self.run()
    
    async def stop(self):
        """Stop the strategy"""
        self.running = False
        logger.info(f"🛑 {self.name} stopped")
    
    async def is_safe_to_trade(self) -> bool:
        """Check if it's safe to open new positions"""
        if self.kill_switch:
            return await self.kill_switch.is_safe_to_trade()
        return True
    
    async def get_position_size(self, symbol: str, side: str) -> float:
        """Calculate position size with dynamic precision from exchange"""
        balance = await self.exchange.get_balance()
        available = balance['free']
        
        # Apply strategy allocation
        allocated = available * self.allocation_pct
        
        # Get current price
        price = await self.exchange.get_perp_price(symbol)
        
        # Calculate size (in base currency)
        size = allocated / price
        
        # Get symbol-specific precision from Binance Futures client
        binance_symbol = symbol.replace("/", "").replace(":USDT", "")
        if hasattr(self.exchange, 'binance_futures') and self.exchange.binance_futures:
            info = self.exchange.binance_futures.get_symbol_info(binance_symbol)
            precision = info.get("quantityPrecision", 3)
            step_size = info.get("stepSize", 0.001)
            min_notional = info.get("minNotional", 100)
            min_qty = info.get("minQty", 0.001)
        else:
            precision = 3
            step_size = 0.001
            min_notional = 100
            min_qty = 0.001
        
        # Round to symbol's precision
        size = round(size, precision)
        
        # Ensure it's a multiple of step size
        if step_size > 0:
            size = round(size / step_size) * step_size
            size = round(size, precision)
        
        # Validate minimum quantity
        if size < min_qty:
            logger.warning(f"{symbol}: Size {size} below minimum {min_qty}. Skipping.")
            return 0
        
        # Validate minimum notional
        notional = size * price
        if notional < min_notional:
            logger.warning(f"{symbol}: Notional ${notional:.2f} below minimum ${min_notional}. Skipping.")
            return 0
        
        return size
    
    async def log_entry(
        self,
        symbol: str,
        side: str,
        price: float,
        size: float,
        meta: Dict = None
    ):
        """Log trade entry"""
        # Store in state
        await self.state.set_position(symbol, {
            'entry_price': price,
            'size': size,
            'side': side,
            'strategy': self.name,
            'entry_time': str(__import__('datetime').datetime.utcnow())
        })
        
        # Log to database
        await self.database.log_trade(
            strategy=self.name,
            symbol=symbol,
            side=side,
            entry_price=price,
            meta_data=meta
        )
        
        # Send alert
        if self.telegram:
            await self.telegram.send_trade_entry(
                strategy=self.name,
                symbol=symbol,
                side=side,
                price=price,
                size=size,
                meta=meta
            )
    
    async def log_exit(
        self,
        symbol: str,
        exit_price: float,
        pnl: float
    ):
        """Log trade exit"""
        pos = await self.state.get_position(symbol)
        if not pos:
            return
        
        entry_price = pos['entry_price']
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        if pos['side'] == 'sell':
            pnl_pct = -pnl_pct
        
        # Remove from state
        await self.state.delete_position(symbol)
        
        # Send alert
        if self.telegram:
            await self.telegram.send_trade_exit(
                strategy=self.name,
                symbol=symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl=pnl,
                pnl_pct=pnl_pct
            )
