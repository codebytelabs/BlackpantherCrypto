#!/usr/bin/env python3
"""Test Gate.io liquidity validation on testnet"""
import asyncio
import sys
sys.path.insert(0, '.')

from core.exchange import ExchangeManager
from loguru import logger

async def test_liquidity():
    """Test liquidity checks on various Gate.io testnet pairs"""
    exchange = ExchangeManager()
    
    try:
        await exchange.connect()
        
        # Test pairs - mix of likely liquid and illiquid
        test_pairs = [
            'BTC/USDT',   # Should be liquid
            'ETH/USDT',   # Should be liquid
            'DOGE/USDT',  # Probably liquid
            'SOL/USDT',   # Probably liquid
            'SHIB/USDT',  # May be illiquid on testnet
            'PEPE/USDT',  # May be illiquid on testnet
        ]
        
        print("\n" + "="*70)
        print("GATE.IO TESTNET LIQUIDITY CHECK")
        print("="*70)
        
        tradeable_count = 0
        
        for symbol in test_pairs:
            try:
                result = await exchange.gate_check_liquidity(symbol)
                
                status = "✅ TRADEABLE" if result['tradeable'] else "❌ SKIP"
                
                print(f"\n{status}: {symbol}")
                print(f"   Spread: {result['spread']:.3f}%")
                print(f"   Bid Depth: ${result['bid_depth']:,.2f}")
                print(f"   Ask Depth: ${result['ask_depth']:,.2f}")
                print(f"   Reason: {result['reason']}")
                
                if result['tradeable']:
                    tradeable_count += 1
                    
            except Exception as e:
                print(f"\n❌ ERROR: {symbol} - {e}")
        
        print("\n" + "="*70)
        print(f"SUMMARY: {tradeable_count}/{len(test_pairs)} pairs tradeable")
        print("="*70)
        
        # Also test the whitelist filter
        print("\n\nTesting whitelist filter...")
        tradeable = await exchange.gate_get_tradeable_pairs()
        print(f"Tradeable pairs from whitelist: {tradeable}")
        
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_liquidity())
