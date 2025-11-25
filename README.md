# 🐆 BlackPanther v2.0 - God Mode

High-frequency algorithmic crypto trading system with three battle-tested strategies.

## 🎯 Strategies

### 1. Cash Cow (40% allocation)
- **Type**: Funding Rate Arbitrage
- **Markets**: Binance Futures + Spot
- **Edge**: Captures funding payments with delta-neutral hedges
- **Target**: 15-30% APY with minimal directional risk

### 2. Trend Killer (30% allocation)
- **Type**: Momentum + Validation
- **Indicators**: SuperTrend + CVD + Open Interest
- **Edge**: Only enters when OI confirms trend strength
- **Target**: High win-rate trend following

### 3. Sniper (30% allocation)
- **Type**: Listing Detection
- **Markets**: Gate.io Spot
- **Edge**: RVOL spikes + Perplexity AI sentiment
- **Target**: Early entry on potential Binance listings

## 🛡️ Risk Management

- **Kill Switch**: Auto-stops at 10% daily drawdown
- **Max Leverage**: 5x
- **Position Sizing**: Dynamic based on symbol precision
- **Latency Monitoring**: Pauses trading on high latency

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/codebytelabs/BlackpantherCrypto.git
cd BlackpantherCrypto/blackpanther

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run tests
python tests/test_all.py

# Start trading
python main.py
```

## 📁 Project Structure

```
blackpanther/
├── core/
│   ├── exchange.py          # Unified exchange interface
│   ├── binance_futures.py   # Custom Binance Futures client
│   ├── state_manager.py     # Redis state management
│   └── database.py          # Supabase trade journal
├── strategies/
│   ├── base.py              # Strategy base class
│   ├── cash_cow.py          # Funding arbitrage
│   ├── trend_killer.py      # Momentum strategy
│   └── sniper.py            # Listing detection
├── risk/
│   └── kill_switch.py       # Risk management
├── intelligence/
│   └── perplexity_client.py # AI sentiment analysis
├── utils/
│   └── indicators.py        # Technical indicators
├── tests/
│   └── test_all.py          # Comprehensive test suite
└── main.py                  # Entry point
```

## 🔑 Required API Keys

- **Binance Spot Testnet**: testnet.binance.vision
- **Binance Futures Testnet**: testnet.binancefuture.com
- **Gate.io Testnet**: Sandbox mode
- **Supabase**: For trade logging
- **Redis**: For state management
- **Perplexity AI**: For sentiment analysis

## 📊 Performance

Testnet validated with:
- Binance Spot: $7,359 USDT
- Binance Futures: $5,000 USDT
- Gate.io: $50,633 USDT
- **Total**: ~$63,000 demo capital

## ⚠️ Disclaimer

This is experimental trading software. Use at your own risk. Never trade with money you can't afford to lose.

## 📜 License

MIT License - See LICENSE file
