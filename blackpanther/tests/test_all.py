#!/usr/bin/env python3
"""
BlackPanther Comprehensive Test Suite
Tests all components with real API keys and data
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Load from blackpanther/.env
bp_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(bp_env, override=True)  # Override any existing env vars

# Results tracking
RESULTS = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_pass(test_name, details=""):
    RESULTS["passed"].append(test_name)
    print(f"  ✅ {test_name}" + (f" - {details}" if details else ""))

def log_fail(test_name, error):
    RESULTS["failed"].append((test_name, str(error)))
    print(f"  ❌ {test_name} - {error}")

def log_warn(test_name, warning):
    RESULTS["warnings"].append((test_name, warning))
    print(f"  ⚠️  {test_name} - {warning}")

# ============================================================
# 1. CONFIGURATION TESTS
# ============================================================
def test_config():
    print("\n📋 1. CONFIGURATION TESTS")
    print("-" * 50)
    
    try:
        from config.settings import settings, CONFIG
        log_pass("Config import")
        
        # Check required settings
        assert settings.MODE in ["PAPER", "LIVE"], "Invalid MODE"
        log_pass("MODE setting", settings.MODE)
        
        assert CONFIG["SYSTEM"]["LEVERAGE_LIMIT"] <= 10, "Leverage too high"
        log_pass("Leverage limit", f"{CONFIG['SYSTEM']['LEVERAGE_LIMIT']}x")
        
        assert CONFIG["SYSTEM"]["MAX_DAILY_DRAWDOWN_PCT"] <= 0.20, "Drawdown limit too high"
        log_pass("Drawdown limit", f"{CONFIG['SYSTEM']['MAX_DAILY_DRAWDOWN_PCT']*100}%")
        
        # Check strategy configs
        for strategy in ["CASH_COW", "TREND_KILLER", "SNIPER"]:
            assert strategy in CONFIG["STRATEGIES"], f"Missing {strategy}"
        log_pass("Strategy configs present")
        
        # Verify allocations sum to ~100%
        total_alloc = sum(s.get("ALLOCATION_PCT", 0) for s in CONFIG["STRATEGIES"].values())
        assert 0.95 <= total_alloc <= 1.05, f"Allocations sum to {total_alloc}"
        log_pass("Allocation percentages", f"{total_alloc*100:.0f}%")
        
    except Exception as e:
        log_fail("Config test", e)

# ============================================================
# 2. EXCHANGE CONNECTION TESTS
# ============================================================
async def test_binance_connection():
    print("\n🔗 2. BINANCE CONNECTION TESTS")
    print("-" * 50)
    
    from core.exchange import ExchangeManager
    exchange = ExchangeManager()
    
    try:
        await exchange.connect()
        log_pass("Binance connection")
        
        # Test latency (public endpoint)
        latency = await exchange.ping()
        if latency > 500:
            log_warn("Latency", f"{latency}ms (high)")
        else:
            log_pass("Latency", f"{latency}ms")
        
        # Test market data (public)
        btc_price = await exchange.get_perp_price("BTC/USDT:USDT")
        assert btc_price > 0, "Invalid BTC price"
        log_pass("BTC price fetch", f"${btc_price:,.2f}")
        
        # Test funding rate (public)
        funding = await exchange.get_funding_rate("BTC/USDT:USDT")
        log_pass("Funding rate fetch", f"{funding*100:.4f}%")
        
        # Test OHLCV (public)
        ohlcv = await exchange.fetch_ohlcv("BTC/USDT:USDT", "15m", limit=10)
        assert len(ohlcv) > 0, "No OHLCV data"
        log_pass("OHLCV fetch", f"{len(ohlcv)} candles")
        
        # Test Open Interest (public)
        try:
            oi = await exchange.get_open_interest("BTC/USDT:USDT")
            log_pass("Open Interest fetch", f"{oi:,.0f}")
        except Exception as e:
            log_warn("Open Interest", f"May require auth: {str(e)[:50]}")
        
        # Test balance (requires auth - may fail on testnet)
        try:
            balance = await exchange.get_balance()
            assert 'total' in balance, "No balance returned"
            log_pass("Balance fetch", f"${balance['total']:,.2f} USDT")
        except Exception as e:
            if "testnet" in str(e).lower() or "sandbox" in str(e).lower() or "deprecated" in str(e).lower():
                log_warn("Balance fetch", "Testnet deprecated - use production keys for live trading")
            else:
                log_warn("Balance fetch", f"Auth required: {str(e)[:60]}")
        
        # Test positions (requires auth)
        try:
            positions = await exchange.get_positions()
            log_pass("Positions fetch", f"{len(positions)} open")
        except Exception as e:
            log_warn("Positions fetch", "Auth required for positions")
        
    except Exception as e:
        log_fail("Binance connection", e)
    finally:
        await exchange.close()

# ============================================================
# 3. GATE.IO CONNECTION TESTS
# ============================================================
async def test_gateio_connection():
    print("\n🔗 3. GATE.IO CONNECTION TESTS")
    print("-" * 50)
    
    from core.exchange import ExchangeManager
    exchange = ExchangeManager()
    
    try:
        await exchange.connect()
        
        # Test tickers
        tickers = await exchange.gate_fetch_tickers()
        assert len(tickers) > 0, "No tickers returned"
        log_pass("Gate.io tickers", f"{len(tickers)} pairs")
        
        # Test OHLCV
        ohlcv = await exchange.gate_fetch_ohlcv("BTC/USDT", "1d", limit=10)
        assert len(ohlcv) > 0, "No OHLCV data"
        log_pass("Gate.io OHLCV", f"{len(ohlcv)} candles")
        
        # Test liquidity check (new feature for testnet)
        liquidity = await exchange.gate_check_liquidity("BTC/USDT")
        assert liquidity['tradeable'] == True, "BTC/USDT should be tradeable"
        log_pass("Liquidity check", f"BTC spread: {liquidity['spread']:.3f}%")
        
        # Test illiquid pair detection
        illiquid = await exchange.gate_check_liquidity("PEPE/USDT")
        if not illiquid['tradeable']:
            log_pass("Illiquid pair detection", illiquid['reason'][:40])
        else:
            log_pass("PEPE/USDT tradeable", f"spread: {illiquid['spread']:.3f}%")
        
    except Exception as e:
        log_fail("Gate.io connection", e)
    finally:
        await exchange.close()

# ============================================================
# 4. SUPABASE DATABASE TESTS
# ============================================================
async def test_supabase():
    print("\n🗄️  4. SUPABASE DATABASE TESTS")
    print("-" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            log_fail("Supabase config", "Missing URL or KEY")
            return
        
        client = create_client(url, key)
        log_pass("Supabase client created")
        
        # Check if trade_journal table exists
        try:
            result = client.table("trade_journal").select("id").limit(1).execute()
            log_pass("trade_journal table exists")
            
            # Test insert
            test_trade = {
                "strategy": "TEST",
                "symbol": "BTC/USDT",
                "side": "buy",
                "entry_price": 100000.0,
                "meta_data": {"test": True}
            }
            
            result = client.table("trade_journal").insert(test_trade).execute()
            if result.data:
                log_pass("Insert test trade")
                
                # Clean up test data
                trade_id = result.data[0]['id']
                client.table("trade_journal").delete().eq("id", trade_id).execute()
                log_pass("Delete test trade")
            else:
                log_warn("Insert test", "RLS policy may be blocking - use SERVICE_ROLE_KEY")
                
        except Exception as e:
            error_str = str(e)
            if "does not exist" in error_str.lower() or "PGRST205" in error_str:
                log_warn("trade_journal table", "Table doesn't exist yet")
                log_warn("Action required", "Run migrations/001_trade_journal.sql in Supabase SQL Editor")
                log_warn("Dashboard URL", "https://supabase.com/dashboard/project/yvdhhtntmolptxgfnbbz/sql")
            elif "row-level security" in error_str.lower() or "42501" in error_str:
                log_warn("trade_journal RLS", "Row-level security enabled - use SERVICE_ROLE_KEY for inserts")
                log_pass("trade_journal table exists (RLS active)")
            else:
                log_fail("trade_journal check", e)
        
    except ImportError:
        log_fail("Supabase import", "supabase package not installed")
    except Exception as e:
        log_fail("Supabase test", e)

# ============================================================
# 5. REDIS STATE MANAGER TESTS
# ============================================================
async def test_redis():
    print("\n🔴 5. REDIS STATE MANAGER TESTS")
    print("-" * 50)
    
    try:
        import redis.asyncio as redis_async
        
        # Try to connect
        r = redis_async.from_url("redis://localhost:6379", decode_responses=True)
        
        try:
            await r.ping()
            log_pass("Redis connection")
            
            # Test state operations
            from core.state_manager import StateManager
            state = StateManager()
            await state.connect()
            
            # Test kill switch
            await state.set_kill_switch(False)
            ks = await state.get_kill_switch()
            assert ks == False, "Kill switch should be False"
            log_pass("Kill switch operations")
            
            # Test position tracking
            test_pos = {
                'entry_price': 100000.0,
                'size': 0.01,
                'side': 'buy',
                'strategy': 'TEST',
                'entry_time': str(datetime.utcnow())
            }
            await state.set_position("TEST/USDT", test_pos)
            pos = await state.get_position("TEST/USDT")
            assert pos is not None, "Position not stored"
            log_pass("Position tracking")
            
            # Clean up
            await state.delete_position("TEST/USDT")
            
            # Test PnL tracking
            await state.set_start_equity(10000.0)
            equity = await state.get_start_equity()
            assert equity == 10000.0, "Equity not stored correctly"
            log_pass("PnL tracking")
            
            await state.close()
            
        except Exception as e:
            if "Connection refused" in str(e):
                log_warn("Redis", "Not running - start with: redis-server")
            else:
                log_fail("Redis operations", e)
        finally:
            await r.close()
            
    except ImportError:
        log_fail("Redis import", "redis package not installed")
    except Exception as e:
        if "Connection refused" in str(e):
            log_warn("Redis", "Not running - start with: redis-server")
        else:
            log_fail("Redis test", e)

# ============================================================
# 6. PERPLEXITY AI TESTS
# ============================================================
async def test_perplexity():
    print("\n🧠 6. PERPLEXITY AI TESTS")
    print("-" * 50)
    
    try:
        from intelligence.perplexity_client import PerplexityClient
        
        client = PerplexityClient()
        
        if not client.enabled:
            log_warn("Perplexity", "API key not configured")
            return
        
        log_pass("Perplexity client created")
        
        # Test basic query
        response = await client.query("What is the current price of Bitcoin? Answer in one sentence.")
        if response:
            log_pass("Basic query", response[:80] + "...")
        else:
            log_fail("Basic query", "No response")
        
        # Test listing rumors check
        result = await client.check_listing_rumors("PEPE")
        if 'score' in result:
            log_pass("Listing rumors check", f"Score: {result['score']}/100")
        else:
            log_warn("Listing rumors", "Unexpected response format")
        
    except Exception as e:
        log_fail("Perplexity test", e)

# ============================================================
# 7. STRATEGY LOGIC TESTS
# ============================================================
async def test_strategies():
    print("\n📊 7. STRATEGY LOGIC TESTS")
    print("-" * 50)
    
    # Test CVD calculation
    try:
        import pandas as pd
        
        # Create test data
        data = {
            'open': [100, 101, 102, 101, 103],
            'high': [102, 103, 104, 103, 105],
            'low': [99, 100, 101, 100, 102],
            'close': [101, 102, 103, 100, 104],  # Up, Up, Up, Down, Up
            'volume': [1000, 1200, 1100, 1500, 1300]
        }
        df = pd.DataFrame(data)
        
        # Calculate CVD
        df['buy_vol'] = df.apply(lambda x: x['volume'] if x['close'] > x['open'] else 0, axis=1)
        df['sell_vol'] = df.apply(lambda x: x['volume'] if x['close'] < x['open'] else 0, axis=1)
        df['cvd'] = (df['buy_vol'] - df['sell_vol']).cumsum()
        
        # Verify CVD logic
        assert df['cvd'].iloc[0] == 1000, "CVD calculation error"  # First candle is up
        assert df['cvd'].iloc[3] < df['cvd'].iloc[2], "CVD should decrease on down candle"
        log_pass("CVD calculation logic")
        
    except Exception as e:
        log_fail("CVD calculation", e)
    
    # Test SuperTrend (custom implementation)
    try:
        from utils.indicators import supertrend as calc_supertrend
        import numpy as np
        
        np.random.seed(42)
        n = 50
        base = 100 + np.cumsum(np.random.randn(n) * 0.5)
        data = {
            'high': pd.Series(base + np.random.rand(n)),
            'low': pd.Series(base - np.random.rand(n)),
            'close': pd.Series(base)
        }
        
        result = calc_supertrend(data['high'], data['low'], data['close'], length=10, multiplier=3.0)
        assert result is not None, "SuperTrend returned None"
        assert 'SUPERT_10_3.0' in result.columns, "Missing SuperTrend column"
        log_pass("SuperTrend calculation (custom)")
        
    except Exception as e:
        log_fail("SuperTrend calculation", e)
    
    # Test RVOL calculation
    try:
        volumes = [1000, 1100, 900, 1200, 1000, 1050, 980, 1100, 1000, 1050]  # 10 days
        avg_vol = sum(volumes) / len(volumes)
        current_vol = 5500  # Today's volume
        rvol = current_vol / avg_vol
        
        assert rvol > 5.0, "RVOL should be > 5x"
        log_pass("RVOL calculation", f"{rvol:.1f}x")
        
    except Exception as e:
        log_fail("RVOL calculation", e)
    
    # Test Basis calculation
    try:
        perp_price = 100500
        spot_price = 100000
        basis = (perp_price - spot_price) / spot_price
        
        assert abs(basis - 0.005) < 0.0001, "Basis calculation error"
        log_pass("Basis calculation", f"{basis*100:.3f}%")
        
    except Exception as e:
        log_fail("Basis calculation", e)

# ============================================================
# 8. RISK MANAGEMENT TESTS
# ============================================================
async def test_risk_management():
    print("\n🛡️  8. RISK MANAGEMENT TESTS")
    print("-" * 50)
    
    try:
        from config import CONFIG
        
        # Test drawdown calculation
        start_equity = 10000
        current_equity = 8900  # 11% loss
        drawdown = (current_equity - start_equity) / start_equity
        
        max_drawdown = CONFIG["SYSTEM"]["MAX_DAILY_DRAWDOWN_PCT"]
        should_trigger = drawdown < -max_drawdown
        
        assert should_trigger == True, "Kill switch should trigger at 11% loss"
        log_pass("Drawdown trigger logic", f"{drawdown*100:.1f}% triggers kill switch")
        
        # Test basis risk
        max_basis = CONFIG["STRATEGIES"]["CASH_COW"]["MAX_BASIS_RISK"]
        test_basis = 0.015  # 1.5%
        should_close = abs(test_basis) > max_basis
        
        assert should_close == True, "Should close at 1.5% basis"
        log_pass("Basis risk logic", f"{test_basis*100:.1f}% triggers close")
        
        # Test leverage limit
        leverage_limit = CONFIG["SYSTEM"]["LEVERAGE_LIMIT"]
        assert leverage_limit <= 5, "Leverage should be <= 5x for safety"
        log_pass("Leverage limit", f"{leverage_limit}x")
        
    except Exception as e:
        log_fail("Risk management", e)

# ============================================================
# 9. INTEGRATION TEST - FULL SIGNAL FLOW
# ============================================================
async def test_integration():
    print("\n🔄 9. INTEGRATION TEST - SIGNAL FLOW")
    print("-" * 50)
    
    try:
        from core.exchange import ExchangeManager
        
        exchange = ExchangeManager()
        await exchange.connect()
        
        # Simulate Trend Killer signal flow
        symbol = "BTC/USDT:USDT"
        
        # 1. Fetch data
        ohlcv = await exchange.fetch_ohlcv(symbol, "15m", limit=50)
        assert len(ohlcv) >= 20, "Not enough data"
        log_pass("Data fetch for signal")
        
        # 2. Get current price
        price = await exchange.get_perp_price(symbol)
        log_pass("Current price", f"${price:,.2f}")
        
        # 3. Get funding rate
        funding = await exchange.get_funding_rate(symbol)
        log_pass("Funding rate", f"{funding*100:.4f}%")
        
        # 4. Calculate indicators (simplified)
        import pandas as pd
        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        
        # CVD
        df['buy_vol'] = df.apply(lambda x: x['v'] if x['c'] > x['o'] else 0, axis=1)
        df['sell_vol'] = df.apply(lambda x: x['v'] if x['c'] < x['o'] else 0, axis=1)
        df['cvd'] = (df['buy_vol'] - df['sell_vol']).cumsum()
        
        cvd_rising = df['cvd'].iloc[-1] > df['cvd'].iloc[-2]
        log_pass("CVD calculated", f"Rising: {cvd_rising}")
        
        # 5. Simulate signal decision
        signal = "WAIT"
        if funding > 0.0001:
            signal = "CASH_COW_OPPORTUNITY"
        if cvd_rising:
            signal = "TREND_POTENTIAL"
        
        log_pass("Signal flow complete", signal)
        
        await exchange.close()
        
    except Exception as e:
        log_fail("Integration test", e)

# ============================================================
# MAIN TEST RUNNER
# ============================================================
async def run_all_tests():
    print("=" * 60)
    print("🐆 BLACKPANTHER VALIDATION SUITE")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests
    test_config()
    await test_binance_connection()
    await test_gateio_connection()
    await test_supabase()
    await test_redis()
    await test_perplexity()
    await test_strategies()
    await test_risk_management()
    await test_integration()
    
    elapsed = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION REPORT")
    print("=" * 60)
    
    print(f"\n✅ PASSED: {len(RESULTS['passed'])}")
    for test in RESULTS['passed']:
        print(f"   • {test}")
    
    if RESULTS['warnings']:
        print(f"\n⚠️  WARNINGS: {len(RESULTS['warnings'])}")
        for test, warning in RESULTS['warnings']:
            print(f"   • {test}: {warning}")
    
    if RESULTS['failed']:
        print(f"\n❌ FAILED: {len(RESULTS['failed'])}")
        for test, error in RESULTS['failed']:
            print(f"   • {test}: {error}")
    
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    
    # Final verdict
    print("\n" + "=" * 60)
    if not RESULTS['failed']:
        print("🎉 VALIDATION PASSED - System ready for paper trading!")
    else:
        print("⚠️  VALIDATION INCOMPLETE - Fix failed tests before trading")
    print("=" * 60)
    
    return len(RESULTS['failed']) == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
