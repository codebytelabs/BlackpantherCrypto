"""Scan Gate.io for RVOL anomalies (Sniper strategy test)"""
import asyncio
import sys
sys.path.insert(0, '..')

from dotenv import load_dotenv
load_dotenv()

from core.exchange import ExchangeManager
from intelligence.perplexity_client import PerplexityClient

async def scan_rvol():
    """
    Scan Gate.io for volume anomalies.
    This is the Sniper strategy's detection logic.
    """
    print("🎯 RVOL Scanner - Gate.io")
    print("=" * 60)
    print("Looking for: RVOL > 3x with price change < 10%")
    print("(Potential insider accumulation patterns)")
    print()
    
    exchange = ExchangeManager()
    perplexity = PerplexityClient()
    
    try:
        await exchange.connect()
        
        print("Fetching tickers...")
        tickers = await exchange.gate_fetch_tickers()
        
        anomalies = []
        
        for symbol, data in tickers.items():
            try:
                # Filter: Only USDT pairs with decent volume
                if '/USDT' not in symbol:
                    continue
                
                quote_vol = data.get('quoteVolume', 0)
                if quote_vol < 100_000 or quote_vol > 100_000_000:
                    continue
                
                # Get historical volume
                ohlcv = await exchange.gate_fetch_ohlcv(symbol, '1d', limit=10)
                if not ohlcv or len(ohlcv) < 5:
                    continue
                
                volumes = [c[5] for c in ohlcv[:-1]]  # Exclude today
                avg_vol = sum(volumes) / len(volumes) if volumes else 0
                
                if avg_vol <= 0:
                    continue
                
                current_vol = data.get('baseVolume', 0)
                rvol = current_vol / avg_vol
                price_change = abs(data.get('percentage', 0))
                
                # RVOL > 3x with price < 10% change
                if rvol > 3.0 and price_change < 10:
                    anomalies.append({
                        'symbol': symbol,
                        'rvol': rvol,
                        'price_change': price_change,
                        'volume_usd': quote_vol,
                        'price': data.get('last', 0)
                    })
                    
            except Exception as e:
                continue
        
        # Sort by RVOL
        anomalies.sort(key=lambda x: x['rvol'], reverse=True)
        
        print(f"\n🔍 Found {len(anomalies)} anomalies:\n")
        
        for i, a in enumerate(anomalies[:10], 1):
            print(f"{i}. {a['symbol']}")
            print(f"   RVOL: {a['rvol']:.1f}x | Price Change: {a['price_change']:.1f}%")
            print(f"   Volume: ${a['volume_usd']:,.0f} | Price: ${a['price']:.6f}")
            
            # Check rumors for top 3
            if i <= 3 and perplexity.enabled:
                print("   Checking rumors...")
                result = await perplexity.check_listing_rumors(a['symbol'])
                print(f"   Rumor Score: {result.get('score', 0)}/100")
            
            print()
        
        if not anomalies:
            print("No significant anomalies found. Market is quiet.")
        
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(scan_rvol())
