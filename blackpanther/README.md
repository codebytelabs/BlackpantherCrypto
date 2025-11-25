# 🐆 BlackPanther v2.0 - God Mode

High-Frequency Algorithmic Trading System for Crypto Markets.

## Architecture

```
40% Capital (Shield) → Cash Cow: Funding Rate Arbitrage + Basis Protection
30% Capital (Sword) → Trend Killer: OI + SuperTrend + CVD Validation  
30% Capital (Nuke)  → Sniper: Gate.io RVOL + Perplexity Sentiment
```

## God Mode Enhancements

1. **Basis Risk Monitor** - Prevents liquidation during funding arb (1% spread limit)
2. **CVD Validation** - Filters fake/wash-trading pumps (lie detector)
3. **RVOL Pre-positioning** - Detects insider accumulation before news

## Quick Start

### 1. Install Dependencies
```bash
cd blackpanther
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Setup Database
Run `migrations/001_trade_journal.sql` in your Supabase SQL Editor.

### 4. Start Redis
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 5. Run (Paper Trading)
```bash
python main.py
```

## Docker Deployment

```bash
docker-compose up -d
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MODE` | PAPER or LIVE | PAPER |
| `MAX_LEVERAGE` | Maximum leverage | 5 |
| `MAX_DAILY_DRAWDOWN_PCT` | Kill switch trigger | 10% |
| `CASH_COW_ENABLED` | Enable funding arb | true |
| `TREND_KILLER_ENABLED` | Enable trend following | true |
| `SNIPER_ENABLED` | Enable listing sniper | true |

## Risk Management

- **Kill Switch**: Auto-shutdown at 10% daily drawdown
- **Basis Monitor**: Force close hedges if spread > 1%
- **Latency Guard**: Pause trading if API latency > 500ms
- **Position Limits**: Max 5% per moonshot trade

## Strategies

### Cash Cow (Funding Arbitrage)
- Short Perp + Long Spot when funding > 0.01%
- Target: 15-30% APY
- Exit: Funding drops or basis blows out

### Trend Killer (OI + CVD)
- Entry: SuperTrend UP + OI surge (>5%) + CVD rising
- Rejects fake pumps where CVD diverges
- Timeframe: 15m

### Sniper (Listing Plays)
- Scans Gate.io for RVOL > 5x with flat price
- Validates with Perplexity AI for listing rumors
- Exit: 50% at 2x, trailing stop on rest

## Monitoring

Telegram alerts for:
- Trade entries/exits
- Signal detections
- Risk warnings
- Daily summaries
- Kill switch triggers

---

*Deploy. 🐆*
