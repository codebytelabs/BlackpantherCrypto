#!/usr/bin/env python3
"""
Test all exchange API keys with their correct endpoints
"""
import asyncio
import ccxt.async_support as ccxt

# API Keys from .env
BINANCE_KEYS = {
    "testnet_v1": {
        "key": "dWZO6yhNISXxR64i2ualU6RxDesrEqedrzXCgwyC6bb5tOd1Abzu8eskPpxVGFMY",
        "secret": "aA0lTYkRhL0ZWsVIhwpCEKszOJpiybJsOUAvYS2tMHkHHaNSGM75cV7iGHjXxeMo",
        "description": "Binance Testnet Keys (first set)"
    },
    "testnet_v2": {
        "key": "kBU1dEZqLrN8E8wbORL4a1qJcjJqdIwWmZpSfK8wrOS2o6jr5bv4u4LrYDsAvAcm",
        "secret": "TaDEx0sN6MepalADn8KRG0bJvJ12EAokw2QX7vZikeOV7e1VVAz7QDPdufpBRLq5",
        "description": "Binance Testnet Keys (second set)"
    }
}

GATEIO_KEYS = {
    "testnet": {
        "key": "84991f4260a91fc2540015ef31a2f063",
        "secret": "172012ca08a7ec9af780b0b56b04f34a7406c6fefc438dfd23de2e8e8384ec1d",
        "description": "Gate.io Testnet Keys"
    }
}

# Endpoints to test
BINANCE_ENDPOINTS = {
    "production_spot": {
        "name": "Binance Production (Spot)",
        "sandbox": False,
        "type": "spot"
    },
    "production_futures": {
        "name": "Binance Production (Futures)",
        "sandbox": False,
        "type": "future"
    },
    "testnet_spot": {
        "name": "Binance Testnet (Spot)",
        "sandbox": True,
        "type": "spot",
        "urls": {
            "api": {
                "public": "https://testnet.binance.vision/api/v3",
                "private": "https://testnet.binance.vision/api/v3",
            }
        }
    },
    "testnet_futures": {
        "name": "Binance Testnet (Futures)",
        "sandbox": False,  # Don't use sandbox flag
        "type": "future",
        "urls": {
            "api": {
                "fapiPublic": "https://testnet.binancefuture.com/fapi/v1",
                "fapiPrivate": "https://testnet.binancefuture.com/fapi/v1",
            }
        }
    }
}

async def test_binance_key(key_name, key_data, endpoint_name, endpoint_config):
    """Test a Binance API key against an endpoint"""
    print(f"\n  Testing {key_name} on {endpoint_config['name']}...")
    
    options = {
        'apiKey': key_data['key'],
        'secret': key_data['secret'],
        'enableRateLimit': True,
        'options': {
            'defaultType': endpoint_config['type'],
            'adjustForTimeDifference': True
        }
    }
    
    if endpoint_config.get('sandbox'):
        options['sandbox'] = True
    
    if endpoint_config.get('urls'):
        options['urls'] = endpoint_config['urls']
    
    exchange = ccxt.binance(options)
    
    try:
        # Test public endpoint first
        await exchange.load_markets()
        print(f"    ✅ Markets loaded ({len(exchange.markets)} pairs)")
        
        # Test private endpoint (balance)
        try:
            balance = await exchange.fetch_balance()
            usdt = balance.get('USDT', {}).get('total', 0) or balance.get('total', {}).get('USDT', 0)
            print(f"    ✅ Balance: {usdt} USDT")
            return True, "Working"
        except Exception as e:
            error = str(e)
            if "Invalid Api-Key" in error or "-2008" in error:
                print(f"    ❌ Invalid API Key for this endpoint")
                return False, "Invalid API Key"
            elif "IP" in error:
                print(f"    ❌ IP not whitelisted")
                return False, "IP not whitelisted"
            else:
                print(f"    ❌ Auth error: {error[:80]}")
                return False, error[:80]
                
    except Exception as e:
        print(f"    ❌ Connection error: {str(e)[:80]}")
        return False, str(e)[:80]
    finally:
        await exchange.close()

async def test_gateio_key(key_name, key_data):
    """Test Gate.io API key"""
    print(f"\n  Testing {key_name}...")
    
    # Gate.io production
    exchange = ccxt.gateio({
        'apiKey': key_data['key'],
        'secret': key_data['secret'],
        'enableRateLimit': True
    })
    
    try:
        await exchange.load_markets()
        print(f"    ✅ Markets loaded ({len(exchange.markets)} pairs)")
        
        try:
            balance = await exchange.fetch_balance()
            usdt = balance.get('USDT', {}).get('total', 0) or balance.get('total', {}).get('USDT', 0)
            print(f"    ✅ Balance: {usdt} USDT")
            return True, "Working"
        except Exception as e:
            error = str(e)
            print(f"    ❌ Auth error: {error[:80]}")
            return False, error[:80]
            
    except Exception as e:
        print(f"    ❌ Connection error: {str(e)[:80]}")
        return False, str(e)[:80]
    finally:
        await exchange.close()

async def test_public_only():
    """Test public endpoints without auth"""
    print("\n📊 Testing Public Endpoints (No Auth Required)")
    print("-" * 50)
    
    # Binance Futures Public
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    try:
        await exchange.load_markets()
        ticker = await exchange.fetch_ticker('BTC/USDT:USDT')
        print(f"  ✅ Binance Futures Public: BTC = ${ticker['last']:,.2f}")
        
        # Funding rate
        funding = await exchange.fetch_funding_rate('BTC/USDT:USDT')
        print(f"  ✅ Funding Rate: {funding['fundingRate']*100:.4f}%")
        
    except Exception as e:
        print(f"  ❌ Binance Public: {e}")
    finally:
        await exchange.close()
    
    # Gate.io Public
    exchange = ccxt.gateio({'enableRateLimit': True})
    
    try:
        await exchange.load_markets()
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(f"  ✅ Gate.io Public: BTC = ${ticker['last']:,.2f}")
    except Exception as e:
        print(f"  ❌ Gate.io Public: {e}")
    finally:
        await exchange.close()

async def main():
    print("=" * 60)
    print("🔑 API KEY VALIDATION TEST")
    print("=" * 60)
    
    results = {
        "binance": {},
        "gateio": {}
    }
    
    # Test public endpoints first
    await test_public_only()
    
    # Test Binance keys
    print("\n\n🟡 BINANCE API KEYS")
    print("=" * 60)
    
    for key_name, key_data in BINANCE_KEYS.items():
        print(f"\n📌 {key_data['description']}")
        
        for endpoint_name, endpoint_config in BINANCE_ENDPOINTS.items():
            success, msg = await test_binance_key(key_name, key_data, endpoint_name, endpoint_config)
            results["binance"][f"{key_name}_{endpoint_name}"] = (success, msg)
            
            if success:
                print(f"    🎉 FOUND WORKING COMBINATION!")
                break
    
    # Test Gate.io keys
    print("\n\n🔵 GATE.IO API KEYS")
    print("=" * 60)
    
    for key_name, key_data in GATEIO_KEYS.items():
        print(f"\n📌 {key_data['description']}")
        success, msg = await test_gateio_key(key_name, key_data)
        results["gateio"][key_name] = (success, msg)
    
    # Summary
    print("\n\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    binance_working = any(s for s, _ in results["binance"].values())
    gateio_working = any(s for s, _ in results["gateio"].values())
    
    print(f"\nBinance: {'✅ Working' if binance_working else '❌ No working keys'}")
    print(f"Gate.io: {'✅ Working' if gateio_working else '❌ No working keys'}")
    
    if not binance_working:
        print("\n" + "=" * 60)
        print("🔧 HOW TO GET BINANCE API KEYS")
        print("=" * 60)
        print("""
For TESTNET (Paper Trading):
1. Go to: https://testnet.binancefuture.com/
2. Login with GitHub
3. Click on API Management (top right)
4. Create new API key
5. Copy Key and Secret

For PRODUCTION (Real Trading):
1. Go to: https://www.binance.com/
2. Login to your account
3. Go to API Management
4. Create new API key (enable Futures if needed)
5. Whitelist your server IP
6. Copy Key and Secret

Note: Testnet keys only work on testnet endpoints!
      Production keys only work on production endpoints!
""")
    
    if not gateio_working:
        print("\n" + "=" * 60)
        print("🔧 HOW TO GET GATE.IO API KEYS")
        print("=" * 60)
        print("""
1. Go to: https://www.gate.io/
2. Login to your account
3. Go to API Management (under Profile)
4. Create new API key
5. Enable Spot Trading permissions
6. Copy Key and Secret
7. Whitelist your IP if required
""")
    
    return binance_working, gateio_working

if __name__ == "__main__":
    asyncio.run(main())
