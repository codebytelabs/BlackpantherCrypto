<div align="center">

# 🐆 BlackPanther v2.0

**High-Frequency Algorithmic Cryptocurrency Trading System**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen.svg)](./blackpanther/tests/)

Multi-strategy portfolio approach combining funding rate arbitrage, momentum validation, and listing detection for consistent returns with minimal directional risk.

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Trading Strategies](#-trading-strategies)
- [Risk Management](#-risk-management)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running Tests](#running-tests)
  - [Starting the Bot](#starting-the-bot)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [API Configuration](#-api-configuration)
- [Performance Metrics](#-performance-metrics)
- [Development](#-development)
  - [Running Tests](#running-tests-1)
  - [Code Style](#code-style)
  - [Adding Strategies](#adding-strategies)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Security](#-security)
- [License](#-license)
- [Disclaimer](#-disclaimer)
- [Support](#-support)

---

## 🎯 Overview

BlackPanther v2.0 is a production-grade algorithmic trading system designed for cryptocurrency markets. It implements a diversified multi-strategy approach to generate consistent returns while managing risk through advanced position sizing, kill switches, and real-time monitoring.

**Key Highlights:**
- 🎯 **Target APY**: 15-30% with minimal directional exposure
- 🛡️ **Risk-First Design**: Automated kill switches and drawdown protection
- 🔄 **Multi-Exchange**: Binance Spot, Binance Futures, Gate.io
- 🧠 **AI-Enhanced**: Perplexity AI for sentiment analysis
- 📊 **Production-Ready**: Comprehensive testing, logging, and monitoring

---

## ✨ Features

- **Multi-Strategy Portfolio**: Three uncorrelated strategies for diversification
- **Exchange Abstraction**: Unified interface for multiple exchanges via CCXT
- **Custom Binance Futures Client**: Direct HTTP implementation for testnet compatibility
- **Real-Time Risk Management**: Kill switch with configurable drawdown limits
- **State Persistence**: Redis-based state management for crash recovery
- **Trade Journaling**: Supabase integration for performance analytics
- **Technical Indicators**: Custom implementations (SuperTrend, CVD, RVOL)
- **AI Sentiment Analysis**: Perplexity API integration for market intelligence
- **Telegram Alerts**: Real-time notifications for trades and system events
- **Comprehensive Testing**: 39 unit and integration tests
- **Docker Support**: Containerized deployment with docker-compose

---

## 📈 Trading Strategies

### 1. Cash Cow (40% allocation)
**Funding Rate Arbitrage**

Exploits funding rate inefficiencies between perpetual futures and spot markets.

- **Type**: Market-neutral arbitrage
- **Markets**: Binance Spot + Binance Futures
- **Entry**: Funding rate > 0.05% (annualized > 15%)
- **Exit**: Rate normalizes or position reaches profit target
- **Risk**: Basis risk monitoring with auto-exit on divergence
- **Target**: 15-30% APY with minimal directional risk

**How it works:**
1. Monitor funding rates across perpetual contracts
2. When rate exceeds threshold, open hedged position (long spot, short futures)
3. Collect funding payments every 8 hours
4. Exit when rate normalizes or basis risk exceeds limits

### 2. Trend Killer (30% allocation)
**Momentum with Multi-Factor Validation**

High-probability trend following with institutional confirmation signals.

- **Type**: Directional momentum
- **Indicators**: SuperTrend (10, 3) + CVD + Open Interest
- **Entry**: SuperTrend signal + CVD confirmation + OI expansion
- **Exit**: SuperTrend reversal or profit target
- **Risk**: Tight stops with trailing mechanism
- **Target**: High win-rate trend capture (>60% accuracy)

**How it works:**
1. SuperTrend identifies trend direction
2. CVD (Cumulative Volume Delta) confirms institutional flow
3. Open Interest expansion validates trend strength
4. Only enters when all three factors align
5. Trails stop-loss to lock in profits

### 3. Sniper (30% allocation)
**Listing Detection & Early Entry**

Identifies potential Binance listings before official announcement.

- **Type**: Event-driven momentum
- **Markets**: Gate.io Spot (pre-listing detection)
- **Signals**: RVOL spikes + Perplexity AI sentiment + social metrics
- **Entry**: RVOL > 3x + positive AI sentiment
- **Exit**: Binance listing announcement or 48-hour timeout
- **Target**: Capture 20-100% pumps on listing announcements

**How it works:**
1. Scan Gate.io for unusual volume spikes (RVOL > 3x)
2. Query Perplexity AI for news and sentiment
3. Validate with social metrics and on-chain data
4. Enter position if all signals align
5. Exit on Binance listing or after 48 hours

---

## 🛡️ Risk Management

BlackPanther implements multiple layers of risk protection:

### Kill Switch
- **Daily Drawdown Limit**: Auto-stops at 10% loss
- **Latency Monitoring**: Pauses trading if execution latency > 500ms
- **Connection Health**: Monitors exchange connectivity
- **Manual Override**: Emergency stop via CLI or Telegram

### Position Management
- **Max Leverage**: 5x (configurable per strategy)
- **Position Sizing**: Dynamic based on account balance and symbol precision
- **Correlation Limits**: Prevents over-concentration in correlated assets
- **Max Open Positions**: 10 concurrent positions across all strategies

### Basis Risk (Cash Cow)
- **Spread Monitoring**: Exits if spot-futures spread > 2%
- **Liquidity Checks**: Ensures sufficient depth before entry
- **Funding Rate Validation**: Confirms rate hasn't reversed

### Execution Protection
- **Slippage Limits**: Rejects orders with excessive slippage
- **Order Timeout**: Cancels unfilled orders after 30 seconds
- **Rate Limiting**: Respects exchange API limits
- **Retry Logic**: Exponential backoff on failures

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **Redis**: For state management
- **Supabase Account**: For trade logging (free tier works)
- **Exchange API Keys**: Binance, Gate.io (testnet recommended for initial testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/BlackpantherCrypto.git
cd BlackpantherCrypto/blackpanther

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Redis (macOS)
brew install redis
brew services start redis

# Or using Docker
docker run -d -p 6379:6379 redis:alpine
```

### Configuration

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Edit `.env` with your credentials:**
```bash
# Exchange API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
BINANCE_FUTURES_API_KEY=your_futures_api_key
BINANCE_FUTURES_API_SECRET=your_futures_secret
GATEIO_API_KEY=your_gateio_api_key
GATEIO_API_SECRET=your_gateio_secret

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI & Alerts
PERPLEXITY_API_KEY=your_perplexity_key
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration
TESTNET=true
MAX_LEVERAGE=5
KILL_SWITCH_DRAWDOWN=0.10
```

3. **Setup database:**
```bash
python scripts/setup_database.py
```

### Running Tests

```bash
# Run all tests
python tests/test_all.py

# Run specific test suites
python tests/test_api_keys.py
python tests/test_binance_futures_complete.py
python tests/test_live_order.py
```

### Starting the Bot

```bash
# Start with default configuration
python main.py

# Or use CLI for more control
python cli.py start --strategies cash_cow,trend_killer

# Monitor status
python cli.py status

# Emergency stop
python cli.py stop
```

---

## 🏗️ Architecture

BlackPanther follows a modular, event-driven architecture:

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│                  (Orchestrator)                         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Cash Cow │  │  Trend   │  │  Sniper  │
│ Strategy │  │  Killer  │  │ Strategy │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌─────────────────┐
│ Exchange Manager│  │  Risk Manager   │
│   (CCXT + BF)   │  │  (Kill Switch)  │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └──────────┬─────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
         ▼          ▼          ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Redis   │  │ Supabase │  │ Telegram │
│  State   │  │  Trades  │  │  Alerts  │
└──────────┘  └──────────┘  └──────────┘
```

### Core Components

- **Exchange Manager**: Unified interface for all exchange operations
- **Strategy Base**: Abstract class defining strategy lifecycle
- **State Manager**: Redis-backed persistence for crash recovery
- **Risk Manager**: Real-time monitoring and kill switch logic
- **Database Layer**: Trade journaling and performance analytics
- **Alert System**: Telegram notifications for critical events

---

## 📁 Project Structure

```
blackpanther/
├── alerts/
│   ├── __init__.py
│   └── telegram.py              # Telegram notification system
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── core/
│   ├── __init__.py
│   ├── exchange.py              # Unified exchange interface (CCXT)
│   ├── binance_futures.py       # Custom Binance Futures client
│   ├── state_manager.py         # Redis state persistence
│   └── database.py              # Supabase trade journal
├── intelligence/
│   ├── __init__.py
│   └── perplexity_client.py     # AI sentiment analysis
├── risk/
│   ├── __init__.py
│   └── kill_switch.py           # Risk management & kill switch
├── strategies/
│   ├── __init__.py
│   ├── base.py                  # Abstract strategy base class
│   ├── cash_cow.py              # Funding rate arbitrage
│   ├── trend_killer.py          # Momentum + validation
│   └── sniper.py                # Listing detection
├── utils/
│   ├── __init__.py
│   └── indicators.py            # Technical indicators (SuperTrend, CVD, RVOL)
├── tests/
│   ├── test_all.py              # Comprehensive test suite (39 tests)
│   ├── test_api_keys.py         # API key validation
│   ├── test_binance_futures_complete.py
│   ├── test_live_order.py       # Live order execution tests
│   └── test_futures_testnet.py
├── scripts/
│   ├── setup_database.py        # Database initialization
│   ├── scan_rvol.py             # RVOL scanner utility
│   └── debug_binance_futures.py # Debugging tools
├── migrations/
│   └── 001_trade_journal.sql    # Database schema
├── logs/                         # Application logs
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Multi-container setup
├── cli.py                        # Command-line interface
├── main.py                       # Application entry point
└── README.md                     # This file
```

---

## 🔑 API Configuration

### Binance Testnet

1. Visit [Binance Spot Testnet](https://testnet.binance.vision/)
2. Create API keys
3. Add to `.env`:
```bash
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

### Binance Futures Testnet

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Create API keys
3. Add to `.env`:
```bash
BINANCE_FUTURES_API_KEY=your_key
BINANCE_FUTURES_API_SECRET=your_secret
```

### Gate.io

1. Visit [Gate.io API Management](https://www.gate.io/myaccount/apiv4keys)
2. Create API keys with trading permissions
3. Add to `.env`:
```bash
GATEIO_API_KEY=your_key
GATEIO_API_SECRET=your_secret
```

### Supabase

1. Create project at [Supabase](https://supabase.com/)
2. Run migration: `python scripts/setup_database.py`
3. Add credentials to `.env`:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
```

### Perplexity AI

1. Get API key from [Perplexity](https://www.perplexity.ai/)
2. Add to `.env`:
```bash
PERPLEXITY_API_KEY=your_key
```

---

## 📊 Performance Metrics

### Testnet Validation

System validated with real testnet capital:

| Exchange | Balance | Status |
|----------|---------|--------|
| Binance Spot | $7,359 USDT | ✅ Connected |
| Binance Futures | $5,000 USDT | ✅ Connected |
| Gate.io | $50,633 USDT | ✅ Connected |
| **Total** | **~$63,000** | **Ready** |

### Test Coverage

- **Total Tests**: 39
- **Pass Rate**: 100%
- **Coverage Areas**:
  - API connectivity and authentication
  - Order placement and execution
  - Strategy signal generation
  - Risk management triggers
  - State persistence and recovery
  - Database operations
  - Indicator calculations

---

## 🛠️ Development

### Running Tests

```bash
# All tests
python tests/test_all.py

# Specific test file
python tests/test_api_keys.py

# With verbose output
python tests/test_all.py -v
```

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

```bash
# Format code
black blackpanther/

# Sort imports
isort blackpanther/

# Lint
flake8 blackpanther/
```

### Adding Strategies

1. Create new file in `strategies/`:
```python
from strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, exchange_manager, state_manager, config):
        super().__init__(exchange_manager, state_manager, config)
        self.name = "my_strategy"
    
    async def generate_signals(self):
        # Your signal logic
        pass
    
    async def execute_trade(self, signal):
        # Your execution logic
        pass
```

2. Register in `main.py`:
```python
from strategies.my_strategy import MyStrategy

strategies = [
    MyStrategy(exchange_manager, state_manager, config)
]
```

3. Add tests in `tests/test_my_strategy.py`

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t blackpanther:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f blackpanther

# Stop
docker-compose down
```

### Production Checklist

- [ ] Set `TESTNET=false` in `.env`
- [ ] Configure production API keys
- [ ] Set appropriate `KILL_SWITCH_DRAWDOWN`
- [ ] Enable Telegram alerts
- [ ] Setup monitoring and logging
- [ ] Configure backup Redis instance
- [ ] Test with small capital first
- [ ] Document emergency procedures

---

## 📡 Monitoring

### Logs

Logs are written to `logs/` directory:
- `blackpanther.log`: Main application log
- `trades.log`: Trade execution log
- `errors.log`: Error and exception log

### Telegram Alerts

Receive real-time notifications for:
- Trade entries and exits
- Kill switch triggers
- System errors
- Daily performance summary

### CLI Monitoring

```bash
# Check system status
python cli.py status

# View recent trades
python cli.py trades --limit 10

# Check positions
python cli.py positions

# View performance
python cli.py performance --days 7
```

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: `401 Unauthorized` on Binance Futures
```bash
# Solution: Regenerate API keys on testnet
# Ensure IP whitelist is configured correctly
```

**Issue**: Redis connection failed
```bash
# Solution: Start Redis service
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

**Issue**: Supabase connection timeout
```bash
# Solution: Check firewall settings
# Verify SUPABASE_URL and SUPABASE_KEY in .env
```

**Issue**: Strategy not generating signals
```bash
# Solution: Check market conditions
python scripts/scan_rvol.py  # For Sniper strategy
# Verify exchange connectivity
python tests/test_api_keys.py
```

### Debug Mode

Enable debug logging in `.env`:
```bash
LOG_LEVEL=DEBUG
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Ensure tests pass**: `python tests/test_all.py`
6. **Format code**: `black blackpanther/`
7. **Commit changes**: `git commit -m 'Add amazing feature'`
8. **Push to branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions and classes
- Write unit tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

---

## 🔒 Security

### Best Practices

- **Never commit API keys** to version control
- **Use testnet** for development and testing
- **Enable IP whitelisting** on exchange API keys
- **Restrict API permissions** (no withdrawal rights needed)
- **Rotate API keys** regularly
- **Monitor for unusual activity**
- **Use strong passwords** for all services

### Reporting Vulnerabilities

If you discover a security vulnerability, please email security@yourproject.com. Do not open a public issue.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 BlackPanther Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ⚠️ Disclaimer

**IMPORTANT: READ CAREFULLY BEFORE USING THIS SOFTWARE**

This software is provided for educational and research purposes only. Cryptocurrency trading carries substantial risk of loss and is not suitable for every investor.

**Key Risks:**
- **Market Risk**: Cryptocurrency markets are highly volatile
- **Execution Risk**: Slippage, latency, and failed orders can occur
- **Technical Risk**: Bugs, API failures, and system crashes are possible
- **Regulatory Risk**: Cryptocurrency regulations vary by jurisdiction
- **Capital Risk**: You can lose all invested capital

**No Guarantees:**
- Past performance does not guarantee future results
- Testnet results may not reflect live trading conditions
- No warranty of profitability or accuracy is provided

**Your Responsibility:**
- Understand the risks before trading
- Never trade with money you cannot afford to lose
- Start with small amounts and testnet first
- Monitor your positions actively
- Comply with local regulations

**No Liability:**
The authors and contributors of this software accept no liability for any losses incurred through the use of this software. Use at your own risk.

---

## 💬 Support

### Documentation

- **Full Documentation**: [docs/](./docs/)
- **API Reference**: [docs/api.md](./docs/api.md)
- **Strategy Guide**: [docs/strategies.md](./docs/strategies.md)

### Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/BlackpantherCrypto/issues)
- **Discussions**: [Join the conversation](https://github.com/yourusername/BlackpantherCrypto/discussions)
- **Telegram**: [Community chat](https://t.me/blackpanther_trading)

### Contact

- **Email**: support@yourproject.com
- **Twitter**: [@blackpanther_bot](https://twitter.com/blackpanther_bot)

---

<div align="center">

**Built with ❤️ by the BlackPanther Team**

⭐ Star us on GitHub if this project helped you!

[Report Bug](https://github.com/yourusername/BlackpantherCrypto/issues) • [Request Feature](https://github.com/yourusername/BlackpantherCrypto/issues) • [Documentation](./docs/)

</div>
