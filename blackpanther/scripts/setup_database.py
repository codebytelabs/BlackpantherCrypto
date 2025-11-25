#!/usr/bin/env python3
"""Setup Supabase database tables for BlackPanther"""
import os
import sys
import httpx

# Load env from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

SQL = """
-- BlackPanther Trade Journal Schema
CREATE TABLE IF NOT EXISTS trade_journal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    strategy VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    pnl_usd DECIMAL(20, 8),
    meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trade_journal_timestamp ON trade_journal(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trade_journal_strategy ON trade_journal(strategy);
CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
"""

def setup_via_rest():
    """Create table using Supabase REST API"""
    print("🗄️  Setting up Supabase database...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return False
    
    # Extract project ref from URL
    # URL format: https://xxxxx.supabase.co
    project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
    
    # Use the SQL endpoint
    sql_url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try direct table creation via supabase client
    try:
        from supabase import create_client
        
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Check if table exists
        try:
            result = client.table("trade_journal").select("id").limit(1).execute()
            print("✅ trade_journal table already exists")
            return True
        except Exception as e:
            if "does not exist" in str(e).lower() or "PGRST205" in str(e):
                print("📝 Table doesn't exist, needs to be created manually")
                print("\n" + "="*60)
                print("Please run this SQL in your Supabase SQL Editor:")
                print("="*60)
                print(SQL)
                print("="*60)
                print(f"\n🔗 Go to: {SUPABASE_URL.replace('.supabase.co', '')}/project/default/sql")
                return False
            else:
                raise
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    setup_via_rest()
