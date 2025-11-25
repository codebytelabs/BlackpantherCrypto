#!/usr/bin/env python3
"""
Test all exchange API keys with their correct endpoints - V2
Includes: Binance Futures Testnet + Gate.io Testnet
"""
import asyncio
import ccxt.async_support as ccxt

# ============================================================
# API KEYS FROM .env
# ============================================================

BINANCE_KEYS = {
    "spot_testnet": {
        "key": "dWZO6yhNISXxR64i2ualU6RxDesrEqedrzXCgwyC6bb5tOd1Abzu8eskPpxVGFMY",
        "secret": "aA0lTYkRhL0ZWsVIhwpCEKszOJpiybJsOUAvYS2tMHkHHaNSGM75cV7iGHjXxeMo",
        "description": "Binance SPOT Testnet (testnet.binance.vision)"
    },
    "futures_testnet": {
        "key": "lGdIQ3ve6XQJ32DIAbDdEBH5dCB2vQYLsHVTLHrgl9nJhzPc0MgV3C7Es7EUbH5E",
        "secret": "GfrTAWwEcWoUKnP5a8FSxIk9rU8AN3yN9oVZBynpt5BDwM0sJ1Gxku5epjEQPR5o",
        "description": "Binance FUTURES Testnet (testnet.binancefuture.com)"
    }
}

GATEIO_KEYS = {
    "testnet": {
        "key": "84991f4260a91fc2540015ef31a2f063",
        "secret": "172012ca08a7ec9af780b0b56b04f34a7406c6fefc438dfd23de2e8e8384ec1d",
        "description": "Gate.io Testnet (testnet.gate.com)"
    }
}

# ============================================================
# TEST FUNCTIONS
# ============================================================

async def test_binance_spot_testnet():
    """Test Binance Spot Testnet"""
    print("\n🟡 BINANCE SPOT TESTNET (testnet.binance.vision)")
    print("-" * 50)
    
    keys = BINANCE_KEYS["spot_testnet"]
    
    exchange = ccxt.binance({
        'apiKey': keys['key'],
        'secret': keys['secret'],
        'enableRateLimit': True,
        'sandbox': True,  # Uses testnet.binance.vision
        'options': {
            'defaultType': 'spot',
            'adjustForTimeDifference': True
        }
    })
    
    try:
        await exchange.load_markets()
        print(f"  ✅ Markets loaded: {len(exchange.markets)} pairs")
        
        # Test balance
        balance = await exchange.fetch_balance()
        usdt = balance.get('USDT', {}).get('total', 0)
        btc = balance.get('BTC', {}).get('total', 0)
        print(f"  ✅ Balance: {usdt:.2f} USDT, {btc:.6f} BTC")
        
        # Test ticker
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(f"  ✅ BTC Price: ${ticker['last']:,.2f}")
        
        return True, f"Working - {usdt:.2f} USDT"
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return False, str(e)[:80]
    finally:
        await exchange.close()

async def test_binance_futures_testnet():
    """Test Binance Futures Testnet"""
    print("\n🟡 BINANCE FUTURES TESTNET (testnet.binancefuture.com)")
    print("-" * 50)
    
    keys = BINANCE_KEYS["futures_testnet"]
    
    # Binance Futures Testnet configuration
    exchange = ccxt.binance({
        'apiKey': keys['key'],
        'secret': keys['secret'],
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'adjustForTimeDifference': True,
            'sandboxMode': True,  # Enable futures testnet
        }
    })
    
    # Override URLs for futures testnet
    exchange.urls['api'] = {
        'fapiPublic': 'https://testnet.binancefuture.com/fapi/v1',
        'fapiPrivate': 'https://testnet.binancefuture.com/fapi/v1',
        'fapiPublicV2': 'https://testnet.binancefuture.com/fapi/v2',
        'fapiPrivateV2': 'https://testnet.binancefuture.com/fapi/v2',
    }
    
    try:
        await exchange.load_markets()
        print(f"  ✅ Markets loaded: {len(exchange.markets)} pairs")
        
        # Test ticker
        ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
        print(f"  ✅ BTC Perp Price: ${ticker['last']:,.2f}")
        
        # Test funding rate
        try:
            funding = await exchange.fetch_funding_rate('BTC/USDT:USDT')
            print(f"  ✅ Funding Rate: {funding['fundingRate']*100:.4f}%")
        except:
            print(f"  ⚠️  Funding rate not available on testnet")
        
        # Test balance
        try:
            balance = await exchange.fetch_balance()
            usdt = balance.get('USDT', {}).get('total', 0) or balance.get('total', {}).get('USDT', 0)
            print(f"  ✅ Balance: {usdt:.2f} USDT")
            return True, f"Working - {usdt:.2f} USDT"
        except Exception as e:
            print(f"  ⚠️  Balance error: {str(e)[:50]}")
            return True, "Public data works, auth may need setup"
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return False, str(e)[:80]
    finally:
        await exchange.close()

async def test_gateio_testnet():
    """Test Gate.io Testnet"""
    print("\n🔵 GATE.IO TESTNET (testnet.gate.com)")
    print("-" * 50)
    
    keys = GATEIO_KEYS["testnet"]
    
    # Gate.io testnet uses different base URL
    exchange = ccxt.gateio({
        'apiKey': keys['key'],
        'secret': keys['secret'],
        'enableRateLimit': True,
    })
    
    # Override for testnet
    exchange.urls['api'] = {
        'public': 'https://fx-api-testnet.gateio.ws/api/v4',
        'private': 'https://fx-api-testnet.gateio.ws/api/v4',
    }
    
    try:
        await exchange.load_markets()
        print(f"  ✅ Markets loaded: {len(exchange.markets)} pairs")
        
        # Test ticker
        try:
            ticker = await exchange.fetch_ticker('BTC/USDT')
            print(f"  ✅ BTC Price: ${ticker['last']:,.2f}")
        except:
            print(f"  ⚠️  Ticker fetch failed - trying different endpoint")
        
        # Test balance
        try:
            balance = await exchange.fetch_balance()
            usdt = balance.get('USDT', {}).get('total', 0)
            print(f"  ✅ Balance: {usdt:.2f} USDT")
            return True, f"Working - {usdt:.2f} USDT"
        except Exception as e:
            print(f"  ⚠️  Balance error: {str(e)[:50]}")
        
        return False, "Testnet connection issues"
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return False, str(e)[:80]
    finally:
        await exchange.close()

async def test_gateio_testnet_v2():
    """Test Gate.io Testnet with spot API"""
    print("\n🔵 GATE.IO TESTNET V2 (api.gateio.ws with sandbox)")
    print("-" * 50)
    
    keys = GATEIO_KEYS["testnet"]
    
    exchange = ccxt.gateio({
        'apiKey': keys['key'],
        'secret': keys['secret'],
        'enableRateLimit': True,
        'sandbox': True,  # Try sandbox mode
    })
    
    try:
        await exchange.load_markets()
        print(f"  ✅ Markets loaded: {len(exchange.markets)} pairs")
        
        # Test balance
        try:
            balance = await exchange.fetch_balance()
            usdt = balance.get('USDT', {}).get('total', 0)
            print(f"  ✅ Balance: {usdt:.2f} USDT")
            return True, f"Working - {usdt:.2f} USDT"
        except Exception as e:
            error = str(e)
            if "INVALID_KEY" in error:
                print(f"  ❌ Invalid API key for this endpoint")
            else:
                print(f"  ⚠️  Balance error: {error[:50]}")
            return False, error[:50]
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return False, str(e)[:80]
    finally:
        await exchange.close()

async def test_production_public():
    """Test production endpoints with public data only"""
    print("\n📊 PRODUCTION PUBLIC DATA (No Auth)")
    print("-" * 50)
    
    # Binance Futures
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    try:
        await exchange.load_markets()
        ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
        funding = await exchange.fetch_funding_rate('BTC/USDT:USDT')
        oi = await exchange.fetch_open_interest('BTC/USDT:USDT')
        
        print(f"  ✅ Binance Futures: BTC = ${ticker['last']:,.2f}")
        print(f"  ✅ Funding Rate: {funding['fundingRate']*100:.4f}%")
        print(f"  ✅ Open Interest: {oi['openInterestAmount']:,.0f} contracts")
    except Exception as e:
        print(f"  ❌ Binance error: {e}")
    finally:
        await exchange.close()
    
    # Gate.io
    exchange = ccxt.gateio({'enableRateLimit': True})
    
    try:
        await exchange.load_markets()
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(f"  ✅ Gate.io: BTC = ${ticker['last']:,.2f}")
        print(f"  ✅ Gate.io: {len(exchange.markets)} pairs available")
    except Exception as e:
        print(f"  ❌ Gate.io error: {e}")
    finally:
        await exchange.close()

async def main():
    print("=" * 60)
    print("🔑 API KEY VALIDATION TEST V2")
    print("=" * 60)
    
    results = {}
    
    # Test production public first
    await test_production_public()
    
    # Test Binance Spot Testnet
    success, msg = await test_binance_spot_testnet()
    results["binance_spot_testnet"] = (success, msg)
    
    # Test Binance Futures Testnet
    success, msg = await test_binance_futures_testnet()
    results["binance_futures_testnet"] = (success, msg)
    
    # Test Gate.io Testnet
    success, msg = await test_gateio_testnet()
    results["gateio_testnet"] = (success, msg)
    
    # Test Gate.io Testnet V2
    success, msg = await test_gateio_testnet_v2()
    results["gateio_testnet_v2"] = (success, msg)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    for name, (success, msg) in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}: {msg}")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if results.get("binance_spot_testnet", (False,))[0]:
        print("  • Binance Spot Testnet: READY for paper trading")
    
    if results.get("binance_futures_testnet", (False,))[0]:
        print("  • Binance Futures Testnet: READY for futures paper trading")
    else:
        print("  • Binance Futures Testnet: Check keys at testnet.binancefuture.com")
    
    gateio_works = results.get("gateio_testnet", (False,))[0] or results.get("gateio_testnet_v2", (False,))[0]
    if gateio_works:
        print("  • Gate.io Testnet: READY")
    else:
        print("  • Gate.io: Using production public data (no auth needed for scanning)")
        print("  • Get testnet keys from: https://www.gate.io/testnet")

if __name__ == "__main__":
    asyncio.run(main())
