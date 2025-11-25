#!/usr/bin/env python3
"""
Debug Binance Futures Testnet Authentication
Identifies and fixes the 401 Unauthorized issue
"""
import asyncio
import httpx
import hmac
import hashlib
import time
import os
import sys
from urllib.parse import urlencode

sys.path.insert(0, '.')
from dotenv import load_dotenv
from pathlib import Path

# Load env - use absolute path
script_dir = Path(__file__).parent.parent
env_path = script_dir / '.env'
print(f"Loading env from: {env_path}")
print(f"Env file exists: {env_path.exists()}")
load_dotenv(env_path, override=True)

# Config - Prioritize FUTURES keys
API_KEY = os.getenv("BINANCE_FUTURES_API_KEY")
API_SECRET = os.getenv("BINANCE_FUTURES_API_SECRET")
BASE_URL = "https://testnet.binancefuture.com"

# Debug: show which keys we're using
print(f"Using BINANCE_FUTURES_API_KEY: {bool(API_KEY)}")
print(f"Using BINANCE_FUTURES_API_SECRET: {bool(API_SECRET)}")

print("=" * 60)
print("BINANCE FUTURES TESTNET DEBUG")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...{API_KEY[-10:]}" if API_KEY else "NOT SET")
print(f"API Secret: {API_SECRET[:10]}...{API_SECRET[-5:]}" if API_SECRET else "NOT SET")
print(f"Base URL: {BASE_URL}")
print("=" * 60)


def sign_params(params: dict, secret: str) -> str:
    """Generate HMAC SHA256 signature"""
    query = urlencode(params)
    signature = hmac.new(
        secret.encode('utf-8'),
        query.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


async def test_server_time():
    """Test 1: Check server time and clock sync"""
    print("\n📡 TEST 1: Server Time & Clock Sync")
    print("-" * 40)
    
    async with httpx.AsyncClient() as client:
        # Get server time
        r = await client.get(f"{BASE_URL}/fapi/v1/time")
        server_time = r.json()["serverTime"]
        local_time = int(time.time() * 1000)
        diff = local_time - server_time
        
        print(f"Server time: {server_time}")
        print(f"Local time:  {local_time}")
        print(f"Difference:  {diff}ms")
        
        if abs(diff) > 1000:
            print("⚠️  WARNING: Clock drift > 1 second! This can cause auth failures.")
            print("   Fix: Sync your system clock with NTP")
        else:
            print("✅ Clock sync OK")
        
        return server_time


async def test_public_endpoint():
    """Test 2: Public endpoint (no auth)"""
    print("\n📡 TEST 2: Public Endpoint (No Auth)")
    print("-" * 40)
    
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/fapi/v1/ticker/price", params={"symbol": "BTCUSDT"})
        if r.status_code == 200:
            data = r.json()
            print(f"✅ BTC Price: ${float(data['price']):,.2f}")
            return True
        else:
            print(f"❌ Failed: {r.status_code} - {r.text}")
            return False


async def test_signed_request_v1(server_time: int = None):
    """Test 3: Signed request with different timestamp approaches"""
    print("\n📡 TEST 3: Signed Request - Balance Endpoint")
    print("-" * 40)
    
    headers = {"X-MBX-APIKEY": API_KEY}
    
    # Try different timestamp approaches
    approaches = [
        ("Local time", int(time.time() * 1000)),
        ("Server time", server_time),
        ("Server time - 500ms", server_time - 500 if server_time else None),
    ]
    
    async with httpx.AsyncClient() as client:
        for name, ts in approaches:
            if ts is None:
                continue
                
            params = {"timestamp": ts}
            params["signature"] = sign_params(params, API_SECRET)
            
            print(f"\n   Trying: {name} (ts={ts})")
            
            r = await client.get(
                f"{BASE_URL}/fapi/v2/balance",
                params=params,
                headers=headers
            )
            
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                for asset in data:
                    if asset["asset"] == "USDT":
                        print(f"   ✅ SUCCESS! USDT Balance: ${float(asset['balance']):,.2f}")
                        return True
            else:
                error = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
                print(f"   ❌ Error: {error}")
    
    return False


async def test_recv_window():
    """Test 4: Try with recvWindow parameter"""
    print("\n📡 TEST 4: Signed Request with recvWindow")
    print("-" * 40)
    
    headers = {"X-MBX-APIKEY": API_KEY}
    
    # recvWindow values to try
    recv_windows = [5000, 10000, 60000]
    
    async with httpx.AsyncClient() as client:
        # Get fresh server time
        r = await client.get(f"{BASE_URL}/fapi/v1/time")
        server_time = r.json()["serverTime"]
        
        for recv in recv_windows:
            params = {
                "timestamp": server_time,
                "recvWindow": recv
            }
            params["signature"] = sign_params(params, API_SECRET)
            
            print(f"\n   Trying recvWindow={recv}ms")
            
            r = await client.get(
                f"{BASE_URL}/fapi/v2/balance",
                params=params,
                headers=headers
            )
            
            if r.status_code == 200:
                data = r.json()
                for asset in data:
                    if asset["asset"] == "USDT":
                        print(f"   ✅ SUCCESS with recvWindow={recv}!")
                        print(f"   USDT Balance: ${float(asset['balance']):,.2f}")
                        return recv
            else:
                error = r.json() if "application/json" in r.headers.get("content-type", "") else r.text
                print(f"   ❌ {r.status_code}: {error}")
    
    return None


async def test_account_info():
    """Test 5: Try account info endpoint instead"""
    print("\n📡 TEST 5: Account Info Endpoint")
    print("-" * 40)
    
    headers = {"X-MBX-APIKEY": API_KEY}
    
    async with httpx.AsyncClient() as client:
        # Get fresh server time
        r = await client.get(f"{BASE_URL}/fapi/v1/time")
        server_time = r.json()["serverTime"]
        
        params = {
            "timestamp": server_time,
            "recvWindow": 60000
        }
        params["signature"] = sign_params(params, API_SECRET)
        
        r = await client.get(
            f"{BASE_URL}/fapi/v2/account",
            params=params,
            headers=headers
        )
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Account info retrieved!")
            print(f"   Total Wallet Balance: ${float(data.get('totalWalletBalance', 0)):,.2f}")
            print(f"   Available Balance: ${float(data.get('availableBalance', 0)):,.2f}")
            return True
        else:
            error = r.json() if "application/json" in r.headers.get("content-type", "") else r.text
            print(f"❌ Error: {error}")
            return False


async def test_api_key_permissions():
    """Test 6: Check if API key has correct permissions"""
    print("\n📡 TEST 6: API Key Validation")
    print("-" * 40)
    
    # The 401 error usually means:
    # 1. Invalid API key
    # 2. API key not enabled for futures
    # 3. IP restriction
    # 4. Signature mismatch
    
    print("Common causes of 401 Unauthorized:")
    print("  1. API key/secret mismatch")
    print("  2. API key not enabled for Futures trading")
    print("  3. IP whitelist restriction")
    print("  4. Testnet keys used on mainnet or vice versa")
    print("  5. Keys expired or revoked")
    print()
    print("To fix:")
    print("  1. Go to https://testnet.binancefuture.com/")
    print("  2. Login and go to API Management")
    print("  3. Generate NEW API keys")
    print("  4. Make sure 'Enable Futures' is checked")
    print("  5. Update .env with new keys")


async def main():
    if not API_KEY or not API_SECRET:
        print("❌ API keys not configured!")
        return
    
    # Run all tests
    server_time = await test_server_time()
    await test_public_endpoint()
    success = await test_signed_request_v1(server_time)
    
    if not success:
        recv = await test_recv_window()
        if recv:
            print(f"\n✅ SOLUTION: Add recvWindow={recv} to all signed requests")
        else:
            await test_account_info()
            await test_api_key_permissions()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
