-- BlackPanther Trade Journal Schema
-- Run this in your Supabase SQL Editor

-- Trade Journal Table
CREATE TABLE IF NOT EXISTS trade_journal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    strategy VARCHAR(20) NOT NULL,  -- 'CASH_COW', 'TREND_KILLER', 'SNIPER'
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,      -- 'buy', 'sell', 'hedge'
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    pnl_usd DECIMAL(20, 8),
    meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast queries
CREATE INDEX IF NOT EXISTS idx_trade_journal_timestamp ON trade_journal(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trade_journal_strategy ON trade_journal(strategy);
CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);

-- Daily PnL Summary View
CREATE OR REPLACE VIEW daily_pnl_summary AS
SELECT 
    DATE(timestamp) as trade_date,
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pnl_usd < 0 THEN 1 ELSE 0 END) as losing_trades,
    SUM(pnl_usd) as total_pnl,
    AVG(pnl_usd) as avg_pnl,
    MAX(pnl_usd) as best_trade,
    MIN(pnl_usd) as worst_trade
FROM trade_journal
WHERE pnl_usd IS NOT NULL
GROUP BY DATE(timestamp), strategy
ORDER BY trade_date DESC;

-- Strategy Performance View
CREATE OR REPLACE VIEW strategy_performance AS
SELECT 
    strategy,
    COUNT(*) as total_trades,
    ROUND(SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric * 100, 2) as win_rate,
    SUM(pnl_usd) as total_pnl,
    AVG(pnl_usd) as avg_pnl,
    STDDEV(pnl_usd) as pnl_stddev
FROM trade_journal
WHERE pnl_usd IS NOT NULL
GROUP BY strategy;

-- Enable Row Level Security (optional but recommended)
ALTER TABLE trade_journal ENABLE ROW LEVEL SECURITY;

-- Policy for authenticated users (adjust as needed)
CREATE POLICY "Allow all for authenticated users" ON trade_journal
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Policy for service role (for the bot)
CREATE POLICY "Allow all for service role" ON trade_journal
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
