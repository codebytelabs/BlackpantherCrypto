# Binance Futures Testnet Setup Guide

## The Problem
Binance has **two separate testnet systems**:
- **Spot Testnet**: `testnet.binance.vision` - For spot trading
- **Futures Testnet**: `testnet.binancefuture.com` - For perpetual futures

**They use different API keys!** Your current keys are for Spot testnet only.

## How to Get Futures Testnet API Keys

### Step 1: Go to Binance Futures Testnet
Open: https://testnet.binancefuture.com/

### Step 2: Login with GitHub
- Click "Log In" in the top right
- Select "Log In with GitHub"
- Authorize the application

### Step 3: Get Test Funds
After logging in, you should automatically receive test USDT.
If not, look for a "Get Test Funds" or "Faucet" button.

### Step 4: Generate API Keys
1. Click on your profile icon (top right)
2. Go to "API Management"
3. Click "Create API"
4. Give it a name like "BlackPanther"
5. Copy both the **API Key** and **Secret Key**

### Step 5: Update Your .env File
Add these lines to `blackpanther/.env`:

```
# Binance Futures Testnet (SEPARATE from Spot!)
BINANCE_FUTURES_API_KEY=your_futures_api_key_here
BINANCE_FUTURES_API_SECRET=your_futures_secret_here
```

### Step 6: Verify
Run the debug script:
```bash
cd blackpanther
python scripts/debug_binance_futures.py
```

You should see:
```
✅ SUCCESS! USDT Balance: $X,XXX.XX
```

## Important Notes

1. **Futures testnet keys are different from Spot testnet keys**
2. **Keys expire** - You may need to regenerate them periodically
3. **IP restrictions** - Make sure no IP whitelist is set, or add your IP
4. **Permissions** - Ensure "Enable Futures" is checked when creating the key

## Troubleshooting

### Error: -2015 "Invalid API-key, IP, or permissions"
- You're using Spot testnet keys on Futures testnet
- Generate new keys from https://testnet.binancefuture.com/

### Error: -1021 "Timestamp outside recv window"
- Your system clock is out of sync
- Run: `sudo sntp -sS time.apple.com` (macOS)

### Error: -2019 "Margin is insufficient"
- Get more test funds from the faucet
- Or reduce position size
