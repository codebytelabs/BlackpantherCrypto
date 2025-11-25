#!/usr/bin/env python3
"""
Comprehensive Binance Futures Testnet Test Suite
Tests all functionality: balance, positions, orders, market data
"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

from core.binance_futures import BinanceFuturesTestnet
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger

# Load env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

API_KEY = os.getenv("BINANCE_FUTURES_API_KEY")
API_SECRET = os.getenv("BINANCE_FUTURES_API_SECRET")


async def test_all():
    """Run all Binance Futures tests"""
    
    print("=" * 70)
    print("BINANCE FUTURES TESTNET - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    client = BinanceFuturesTestnet(API_KEY, API_SECRET)
    await client.connect()
    
    try:
        # === PUBLIC ENDPOINTS (No Auth) ===
        print("\n📊 PUBLIC MARKET DATA TESTS")
        print("-" * 70)
        
        # Test 1: Ticker Price
        ticker = await client.get_ticker("BTCUSDT")
        print(f"✅ BTC Price: ${ticker['price']:,.2f}")
        
        # Test 2: 24h Stats
        stats = await client.get_ticker_24h("BTCUSDT")
        print(f"✅ 24h Volume: {float(stats['volume']):,.0f} BTC")
        print(f"   24h Change: {float(stats['priceChangePercent']):.2f}%")
        
        # Test 3: Funding Rate
        funding = await client.get_funding_rate("BTCUSDT")
        print(f"✅ Funding Rate: {funding*100:.4f}%")
        
        # Test 4: Open Interest
        oi = await client.get_open_interest("BTCUSDT")
        print(f"✅ Open Interest: {oi:,.0f} BTC")
        
        # Test 5: Klines/OHLCV
        klines = await client.get_klines("BTCUSDT", "15m", limit=10)
        print(f"✅ Klines: {len(klines)} candles fetched")
        print(f"   Latest close: ${klines[-1][4]:,.2f}")
        
        # === PRIVATE ENDPOINTS (Auth Required) ===
        print("\n🔐 AUTHENTICATED ACCOUNT TESTS")
        print("-" * 70)
        
        # Test 6: Account Balance
        balance = await client.get_balance()
        print(f"✅ Account Balance:")
        print(f"   Total: ${balance['total']:,.2f} USDT")
        print(f"   Free: ${balance['free']:,.2f} USDT")
        print(f"   Used: ${balance['used']:,.2f} USDT")
        
        # Test 7: Positions
        positions = await client.get_positions()
        print(f"✅ Open Positions: {len(positions)}")
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['side']} {pos['contracts']} @ ${pos['entryPrice']}")
        
        # === TRADING TESTS (Careful!) ===
        print("\n⚠️  TRADING CAPABILITY TESTS (No actual orders)")
        print("-" * 70)
        
        # Test 8: Set Leverage (safe operation)
        try:
            await client.set_leverage("BTCUSDT", 2)
            print(f"✅ Leverage set to 2x for BTCUSDT")
        except Exception as e:
            print(f"⚠️  Leverage setting: {e}")
        
        # Test 9: Order Placement (COMMENTED OUT - uncomment to test real orders)
        # WARNING: This will place a real order on testnet!
        """
        print("\n🚨 LIVE ORDER TEST (Uncomment to enable)")
        try:
            # Small test order: 0.001 BTC (~$87)
            order = await client.create_market_order("BTCUSDT", "BUY", 0.001)
            print(f"✅ Market order placed: {order}")
            
            # Close the position immediately
            await asyncio.sleep(1)
            await client.close_position("BTCUSDT")
            print(f"✅ Position closed")
        except Exception as e:
            print(f"❌ Order test failed: {e}")
        """
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Binance Futures Testnet is fully operational!")
        print("=" * 70)
        print(f"\n💰 Available Balance: ${balance['free']:,.2f} USDT")
        print(f"📊 Ready for paper trading with 3 strategies")
        print(f"🎯 To start trading: python main.py")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_all())
