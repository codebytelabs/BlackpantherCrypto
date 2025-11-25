#!/usr/bin/env python3
"""
BlackPanther CLI - Quick commands for managing the trading system
"""
import asyncio
import sys
import argparse
from dotenv import load_dotenv
load_dotenv()

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="<level>{message}</level>", level="INFO")

async def cmd_status():
    """Check system status"""
    from core.exchange import ExchangeManager
    from core.state_manager import StateManager
    
    print("🐆 BlackPanther Status")
    print("=" * 50)
    
    exchange = ExchangeManager()
    state = StateManager()
    
    try:
        await exchange.connect()
        await state.connect()
        
        # Balance
        balance = await exchange.get_balance()
        print(f"\n💰 Balance: ${balance['total']:,.2f} USDT")
        print(f"   Free: ${balance['free']:,.2f}")
        print(f"   Used: ${balance['used']:,.2f}")
        
        # Latency
        latency = await exchange.ping()
        print(f"\n⚡ Latency: {latency}ms")
        
        # Kill switch
        kill_active = await state.get_kill_switch()
        print(f"\n🛡️ Kill Switch: {'🔴 ACTIVE' if kill_active else '🟢 Inactive'}")
        
        # Daily PnL
        daily_pnl = await state.get_daily_pnl()
        start_equity = await state.get_start_equity()
        if start_equity > 0:
            pnl_pct = (daily_pnl / start_equity) * 100
            print(f"\n📊 Daily PnL: ${daily_pnl:,.2f} ({pnl_pct:+.2f}%)")
        
        # Positions
        positions = await state.get_all_positions()
        print(f"\n📈 Active Positions: {len(positions)}")
        for symbol, pos in positions.items():
            print(f"   {symbol}: {pos['side']} @ ${pos['entry_price']:,.2f}")
        
    finally:
        await exchange.close()
        await state.close()

async def cmd_prices():
    """Show current prices"""
    from core.exchange import ExchangeManager
    
    exchange = ExchangeManager()
    await exchange.connect()
    
    symbols = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]
    
    print("📊 Current Prices")
    print("=" * 50)
    
    for symbol in symbols:
        try:
            price = await exchange.get_perp_price(symbol)
            funding = await exchange.get_funding_rate(symbol)
            print(f"{symbol.split('/')[0]}: ${price:,.2f} | Funding: {funding*100:.4f}%")
        except:
            pass
    
    await exchange.close()

async def cmd_funding():
    """Show funding rates"""
    from core.exchange import ExchangeManager
    
    exchange = ExchangeManager()
    await exchange.connect()
    
    symbols = [
        "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT",
        "DOGE/USDT:USDT", "XRP/USDT:USDT", "AVAX/USDT:USDT"
    ]
    
    print("💰 Funding Rates (8h)")
    print("=" * 50)
    
    rates = []
    for symbol in symbols:
        try:
            funding = await exchange.get_funding_rate(symbol)
            apy = funding * 3 * 365 * 100
            rates.append((symbol, funding, apy))
        except:
            pass
    
    # Sort by funding rate
    rates.sort(key=lambda x: x[1], reverse=True)
    
    for symbol, funding, apy in rates:
        emoji = "🟢" if funding > 0.0001 else "⚪"
        print(f"{emoji} {symbol.split('/')[0]:6} | {funding*100:+.4f}% | APY: {apy:+.1f}%")
    
    await exchange.close()

async def cmd_reset_killswitch():
    """Reset the kill switch"""
    from core.state_manager import StateManager
    
    state = StateManager()
    await state.connect()
    
    await state.set_kill_switch(False)
    print("✅ Kill switch reset")
    
    await state.close()

async def cmd_close_all():
    """Close all positions (emergency)"""
    from core.exchange import ExchangeManager
    
    exchange = ExchangeManager()
    await exchange.connect()
    
    print("🚨 Closing all positions...")
    
    await exchange.cancel_all_orders()
    print("   Orders cancelled")
    
    positions = await exchange.get_positions()
    for pos in positions:
        await exchange.close_position(pos['symbol'])
        print(f"   Closed {pos['symbol']}")
    
    print("✅ All positions closed")
    
    await exchange.close()

def main():
    parser = argparse.ArgumentParser(description="🐆 BlackPanther CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    subparsers.add_parser('status', help='Check system status')
    subparsers.add_parser('prices', help='Show current prices')
    subparsers.add_parser('funding', help='Show funding rates')
    subparsers.add_parser('reset', help='Reset kill switch')
    subparsers.add_parser('close-all', help='Close all positions (emergency)')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        asyncio.run(cmd_status())
    elif args.command == 'prices':
        asyncio.run(cmd_prices())
    elif args.command == 'funding':
        asyncio.run(cmd_funding())
    elif args.command == 'reset':
        asyncio.run(cmd_reset_killswitch())
    elif args.command == 'close-all':
        confirm = input("⚠️  This will close ALL positions. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            asyncio.run(cmd_close_all())
        else:
            print("Cancelled")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
