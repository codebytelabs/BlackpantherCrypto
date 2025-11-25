"""
🐆 BLACKPANTHER: HIGH-FREQUENCY ALGORITHMIC TRADING SYSTEM
Version: 2.0 (God Mode)

Triple-Filter Validation:
1. Basis Risk Monitoring (Prevents liquidation during funding arb)
2. CVD Validation (Filters fake/wash-trading pumps)
3. RVOL Pre-positioning (Detects insider accumulation)
"""
import asyncio
import sys
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config import settings, CONFIG
from core.exchange import ExchangeManager
from core.state_manager import StateManager
from core.database import DatabaseManager
from risk.kill_switch import KillSwitch
from alerts.telegram import TelegramAlert
from strategies import CashCowStrategy, TrendKillerStrategy, SniperStrategy

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/blackpanther_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)

class BlackPanther:
    """Main orchestrator for the trading system"""
    
    def __init__(self):
        # Core components
        self.exchange = ExchangeManager()
        self.state = StateManager()
        self.database = DatabaseManager()
        self.telegram = TelegramAlert()
        self.kill_switch = None
        
        # Strategies
        self.strategies = []
        
        # Running state
        self.running = False
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("🐆 Initializing BlackPanther...")
        
        # Connect to services
        await self.exchange.connect()
        await self.state.connect()
        await self.database.connect()
        
        # Initialize kill switch
        self.kill_switch = KillSwitch(
            exchange=self.exchange,
            state=self.state,
            telegram=self.telegram
        )
        
        # Initialize strategies based on config
        strategy_args = {
            'exchange': self.exchange,
            'state': self.state,
            'database': self.database,
            'telegram': self.telegram,
            'kill_switch': self.kill_switch
        }
        
        if CONFIG["STRATEGIES"]["CASH_COW"]["ENABLED"]:
            self.strategies.append(CashCowStrategy(**strategy_args))
            logger.info("💰 Cash Cow strategy enabled (40% allocation)")
        
        if CONFIG["STRATEGIES"]["TREND_KILLER"]["ENABLED"]:
            self.strategies.append(TrendKillerStrategy(**strategy_args))
            logger.info("⚔️ Trend Killer strategy enabled (30% allocation)")
        
        if CONFIG["STRATEGIES"]["SNIPER"]["ENABLED"]:
            self.strategies.append(SniperStrategy(**strategy_args))
            logger.info("🎯 Sniper strategy enabled (30% allocation)")
        
        # Get initial balance
        balance = await self.exchange.get_balance()
        logger.info(f"💵 Starting equity: ${balance['total']:,.2f}")
        
        # Send startup notification
        await self.telegram.send_startup(
            mode=settings.MODE,
            strategies=[s.name for s in self.strategies]
        )
        
        logger.info("✅ BlackPanther initialized")
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        logger.info("🚀 BlackPanther God Mode ACTIVATED")
        logger.info(f"📊 Mode: {settings.MODE}")
        logger.info(f"🛡️ Max Drawdown: {CONFIG['SYSTEM']['MAX_DAILY_DRAWDOWN_PCT']*100}%")
        logger.info(f"⚡ Max Leverage: {CONFIG['SYSTEM']['LEVERAGE_LIMIT']}x")
        
        try:
            # Create tasks for all components
            tasks = [
                asyncio.create_task(self.kill_switch.start()),
            ]
            
            # Add strategy tasks
            for strategy in self.strategies:
                tasks.append(asyncio.create_task(strategy.start()))
            
            # Run until interrupted
            await asyncio.gather(*tasks)
            
        except asyncio.CancelledError:
            logger.info("Shutdown signal received")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            await self.kill_switch.manual_shutdown(f"Fatal error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down BlackPanther...")
        
        self.running = False
        
        # Stop strategies
        for strategy in self.strategies:
            await strategy.stop()
        
        # Stop kill switch
        if self.kill_switch:
            await self.kill_switch.stop()
        
        # Close connections
        await self.exchange.close()
        await self.state.close()
        
        logger.info("👋 BlackPanther shutdown complete")

async def main():
    """Entry point"""
    panther = BlackPanther()
    
    try:
        await panther.initialize()
        await panther.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        await panther.shutdown()

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🐆 BLACKPANTHER v2.0 - GOD MODE                           ║
    ║                                                              ║
    ║   High-Frequency Algorithmic Trading System                  ║
    ║   Target Markets: Binance Futures | Gate.io Spot            ║
    ║                                                              ║
    ║   Strategies:                                                ║
    ║   • Cash Cow (40%) - Funding Rate Arbitrage                 ║
    ║   • Trend Killer (30%) - OI + SuperTrend + CVD              ║
    ║   • Sniper (30%) - Gate.io RVOL + Sentiment                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
