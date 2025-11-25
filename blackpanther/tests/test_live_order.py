#!/usr/bin/env python3
"""
Test LIVE order execution on testnet exchanges.
This will place and cancel real orders using demo money.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.exchange import ExchangeManager
from loguru import logger

async def test_binance_spot_order():
    """Test placing a real order on Binance Testnet"""
    print("\n" + "=" * 60)
    print("🔥 LIVE ORDER TEST - BINANCE TESTNET")
    print("=" * 60)
    
    exchange = ExchangeManager()
    
    try:
        await exchange.connect()
        
        # Check balance before
        balance = await exchange.get_balance()
        print(f"\n💰 Balance BEFORE: ${balance['total']:,.2f} USDT")
        
        # Get current BTC price
        ticker = await exchange.binance.fetch_ticker('BTC/USDT')
        btc_price = ticker['last']
        print(f"📊 BTC Price: ${btc_price:,.2f}")
        
        # Place a small LIMIT BUY order (won't fill immediately)
        # Set price 5% below market so it doesn't fill
        limit_price = btc_price * 0.95
        amount = 0.0001  # Minimum order size
        
        print(f"\n📝 Placing LIMIT BUY order:")
        print(f"   Symbol: BTC/USDT")
        print(f"   Side: BUY")
        print(f"   Amount: {amount} BTC")
        print(f"   Price: ${limit_price:,.2f} (5% below market)")
        
        order = await exchange.binance.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=amount,
            price=limit_price
        )
        
        print(f"\n✅ ORDER PLACED!")
        print(f"   Order ID: {order['id']}")
        print(f"   Status: {order['status']}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Cancel the order
        print(f"\n🚫 Cancelling order...")
        cancel = await exchange.binance.cancel_order(order['id'], 'BTC/USDT')
        print(f"✅ Order cancelled: {cancel['status']}")
        
        # Check balance after
        balance = await exchange.get_balance()
        print(f"\n💰 Balance AFTER: ${balance['total']:,.2f} USDT")
        
        print("\n" + "=" * 60)
        print("🎉 BINANCE TESTNET ORDER TEST PASSED!")
        print("   Real orders are being executed on the testnet.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        await exchange.close()

async def test_gateio_spot_order():
    """Test placing a real order on Gate.io Testnet"""
    print("\n" + "=" * 60)
    print("🔥 LIVE ORDER TEST - GATE.IO TESTNET")
    print("=" * 60)
    
    exchange = ExchangeManager()
    
    try:
        await exchange.connect()
        
        # Check balance
        balance = await exchange.gate.fetch_balance()
        usdt = balance.get('USDT', {}).get('total', 0)
        print(f"\n💰 Balance: {usdt:,.2f} USDT")
        
        # Get current BTC price
        ticker = await exchange.gate.fetch_ticker('BTC/USDT')
        btc_price = ticker['last']
        print(f"📊 BTC Price: ${btc_price:,.2f}")
        
        # Place a small LIMIT BUY order
        limit_price = btc_price * 0.95
        amount = 0.0001
        
        print(f"\n📝 Placing LIMIT BUY order:")
        print(f"   Symbol: BTC/USDT")
        print(f"   Amount: {amount} BTC")
        print(f"   Price: ${limit_price:,.2f}")
        
        order = await exchange.gate.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=amount,
            price=limit_price
        )
        
        print(f"\n✅ ORDER PLACED!")
        print(f"   Order ID: {order['id']}")
        print(f"   Status: {order['status']}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Cancel the order
        print(f"\n🚫 Cancelling order...")
        cancel = await exchange.gate.cancel_order(order['id'], 'BTC/USDT')
        print(f"✅ Order cancelled")
        
        print("\n" + "=" * 60)
        print("🎉 GATE.IO TESTNET ORDER TEST PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        await exchange.close()

async def main():
    print("=" * 60)
    print("🐆 BLACKPANTHER - LIVE ORDER EXECUTION TEST")
    print("=" * 60)
    print("\nThis test will place REAL orders on testnet exchanges")
    print("using your demo money. Orders will be cancelled immediately.")
    
    binance_ok = await test_binance_spot_order()
    gateio_ok = await test_gateio_spot_order()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"Binance Testnet: {'✅ WORKING' if binance_ok else '❌ FAILED'}")
    print(f"Gate.io Testnet: {'✅ WORKING' if gateio_ok else '❌ FAILED'}")
    
    if binance_ok and gateio_ok:
        print("\n🎉 All exchanges ready for live trading on testnet!")
    
    return binance_ok and gateio_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
