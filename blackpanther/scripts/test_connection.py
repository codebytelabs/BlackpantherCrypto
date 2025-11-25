"""Test exchange connections and API keys"""
import asyncio
import sys
sys.path.insert(0, '..')

from dotenv import load_dotenv
load_dotenv()

from core.exchange import ExchangeManager
from config import settings

async def test():
    print("🐆 BlackPanther Connection Test")
    print("=" * 50)
    
    exchange = ExchangeManager()
    
    try:
        print("\n1. Connecting to exchanges...")
        await exchange.connect()
        print("   ✅ Connected!")
        
        print("\n2. Testing Binance Futures...")
        balance = await exchange.get_balance()
        print(f"   Balance: ${balance['total']:,.2f} USDT")
        
        latency = await exchange.ping()
        print(f"   Latency: {latency}ms")
        
        print("\n3. Testing market data...")
        btc_price = await exchange.get_perp_price("BTC/USDT:USDT")
        print(f"   BTC Price: ${btc_price:,.2f}")
        
        funding = await exchange.get_funding_rate("BTC/USDT:USDT")
        print(f"   BTC Funding: {funding*100:.4f}%")
        
        oi = await exchange.get_open_interest("BTC/USDT:USDT")
        print(f"   BTC Open Interest: {oi:,.0f}")
        
        print("\n4. Testing Gate.io...")
        tickers = await exchange.gate_fetch_tickers()
        print(f"   Found {len(tickers)} trading pairs")
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Ready to trade.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(test())
