#!/usr/bin/env python3
"""
Test Binance Futures Testnet connectivity
Endpoint: testnet.binancefuture.com
"""
import asyncio
import ccxt.async_support as ccxt

# Futures testnet keys from .env
FUTURES_KEY = "lGdIQ3ve6XQJ32DIAbDdEBH5dCB2vQYLsHVTLHrgl9nJhzPc0MgV3C7Es7EUbH5E"
FUTURES_SECRET = "GfrTAWwEcWoUKnP5a8FSxIk9rU8AN3yN9oVZBynpt5BDwM0sJ1Gxku5epjEQPR5o"

async def test_futures_testnet():
    print("=" * 60)
    print("🔥 BINANCE FUTURES TESTNET TEST")
    print("=" * 60)
    
    # Method 1: Using binanceusdm (USDT-M Futures)
    print("\n📌 Method 1: binanceusdm with custom URLs")
    
    exchange = ccxt.binanceusdm({
        'apiKey': FUTURES_KEY,
        'secret': FUTURES_SECRET,
        'enableRateLimit': True,
        'options': {
            'adjustForTimeDifference': True,
        }
    })
    
    # Override URLs for testnet
    exchange.urls['api'] = {
        'fapiPublic': 'https://testnet.binancefuture.com/fapi/v1',
        'fapiPrivate': 'https://testnet.binancefuture.com/fapi/v1',
        'fapiPublicV2': 'https://testnet.binancefuture.com/fapi/v2',
        'fapiPrivateV2': 'https://testnet.binancefuture.com/fapi/v2',
        'public': 'https://testnet.binancefuture.com/fapi/v1',
        'private': 'https://testnet.binancefuture.com/fapi/v1',
    }
    
    try:
        await exchange.load_markets()
        print(f"  ✅ Markets loaded: {len(exchange.markets)} pairs")
        
        # Test ticker
        ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
        print(f"  ✅ BTC Perp Price: ${ticker['last']:,.2f}")
        
        # Test balance
        try:
            balance = await exchange.fetch_balance()
            usdt = balance.get('USDT', {}).get('total', 0) or balance.get('total', {}).get('USDT', 0)
            print(f"  ✅ Futures Balance: {usdt} USDT")
        except Exception as e:
            print(f"  ⚠️ Balance error: {str(e)[:60]}")
        
        # Test positions
        try:
            positions = await exchange.fetch_positions()
            open_pos = [p for p in positions if float(p.get('contracts', 0)) > 0]
            print(f"  ✅ Open Positions: {len(open_pos)}")
        except Exception as e:
            print(f"  ⚠️ Positions error: {str(e)[:60]}")
        
        # Test placing a futures order
        print("\n📝 Testing Futures Order...")
        try:
            # Set leverage first
            await exchange.set_leverage(5, 'BTC/USDT:USDT')
            print("  ✅ Leverage set to 5x")
            
            # Place a limit order far from market
            limit_price = ticker['last'] * 0.90  # 10% below
            
            order = await exchange.create_order(
                symbol='BTC/USDT:USDT',
                type='limit',
                side='buy',
                amount=0.001,
                price=limit_price
            )
            print(f"  ✅ Futures Order Placed! ID: {order['id']}")
            
            # Cancel it
            await asyncio.sleep(1)
            await exchange.cancel_order(order['id'], 'BTC/USDT:USDT')
            print("  ✅ Order Cancelled")
            
        except Exception as e:
            print(f"  ❌ Order error: {str(e)[:80]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return False
    finally:
        await exchange.close()

async def test_futures_via_binance():
    """Try using regular binance with futures type"""
    print("\n📌 Method 2: binance with defaultType=future")
    
    exchange = ccxt.binance({
        'apiKey': FUTURES_KEY,
        'secret': FUTURES_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'adjustForTimeDifference': True,
        }
    })
    
    # Set testnet URLs
    exchange.set_sandbox_mode(True)
    
    try:
        await exchange.load_markets()
        print(f"  ✅ Markets loaded")
        
        balance = await exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('total', 0)
        print(f"  ✅ Balance: {usdt} USDT")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return False
    finally:
        await exchange.close()

async def main():
    m1 = await test_futures_testnet()
    m2 = await test_futures_via_binance()
    
    print("\n" + "=" * 60)
    print("📋 RESULTS")
    print("=" * 60)
    print(f"Method 1 (binanceusdm + custom URLs): {'✅' if m1 else '❌'}")
    print(f"Method 2 (binance + sandbox): {'✅' if m2 else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())
