"""BlackPanther - Perplexity AI Client for Sentiment Analysis"""
import httpx
from loguru import logger
from config import settings
from typing import Optional, Dict

class PerplexityClient:
    """Perplexity Sonar API for real-time sentiment and rumor detection"""
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.model = "sonar-pro"
        self.enabled = bool(self.api_key)
        
    async def query(self, prompt: str) -> Optional[str]:
        """Send a query to Perplexity"""
        if not self.enabled:
            logger.warning("Perplexity API not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a crypto market analyst. Provide concise, factual analysis."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.2,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"Perplexity API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Perplexity query failed: {e}")
            return None
    
    async def check_listing_rumors(self, symbol: str) -> Dict:
        """
        Check for Binance listing rumors for a token.
        Returns sentiment score and summary.
        """
        # Clean symbol (remove /USDT etc)
        token = symbol.split("/")[0].upper()
        
        prompt = f"""
        Search Twitter, Telegram, and crypto news for any rumors about {token} being listed on Binance.
        
        Analyze:
        1. Are there credible rumors about a Binance listing?
        2. What is the source quality (official, influencer, random)?
        3. How recent are these rumors?
        
        Respond with:
        - SCORE: 0-100 (0 = no rumors, 100 = confirmed listing)
        - SUMMARY: One sentence summary
        - SOURCES: Key sources found
        """
        
        response = await self.query(prompt)
        
        if not response:
            return {"score": 0, "summary": "Unable to analyze", "sources": []}
        
        # Parse response (simple extraction)
        score = self._extract_score(response)
        
        return {
            "score": score,
            "summary": response[:200],
            "raw_response": response
        }
    
    async def analyze_token_sentiment(self, symbol: str) -> Dict:
        """
        General sentiment analysis for a token.
        """
        token = symbol.split("/")[0].upper()
        
        prompt = f"""
        Analyze current market sentiment for {token} cryptocurrency.
        
        Consider:
        1. Recent news and announcements
        2. Social media sentiment (Twitter, Reddit)
        3. On-chain activity if notable
        4. Any upcoming events or catalysts
        
        Respond with:
        - SENTIMENT: BULLISH / BEARISH / NEUTRAL
        - SCORE: 0-100 (0 = extremely bearish, 100 = extremely bullish)
        - KEY_FACTORS: Top 3 factors affecting sentiment
        """
        
        response = await self.query(prompt)
        
        if not response:
            return {"sentiment": "NEUTRAL", "score": 50, "factors": []}
        
        score = self._extract_score(response)
        sentiment = "BULLISH" if score > 60 else "BEARISH" if score < 40 else "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "score": score,
            "summary": response[:300],
            "raw_response": response
        }
    
    async def check_whale_activity(self, symbol: str) -> Dict:
        """
        Check for notable whale activity on a token.
        """
        token = symbol.split("/")[0].upper()
        
        prompt = f"""
        Search for recent whale activity and large transactions for {token}.
        
        Look for:
        1. Large exchange deposits/withdrawals
        2. Whale wallet movements
        3. Unusual accumulation patterns
        
        Respond with:
        - ACTIVITY_LEVEL: HIGH / MEDIUM / LOW
        - DIRECTION: ACCUMULATING / DISTRIBUTING / NEUTRAL
        - NOTABLE_EVENTS: Any specific large transactions
        """
        
        response = await self.query(prompt)
        
        if not response:
            return {"activity": "LOW", "direction": "NEUTRAL", "events": []}
        
        return {
            "summary": response[:300],
            "raw_response": response
        }
    
    def _extract_score(self, text: str) -> int:
        """Extract numeric score from response"""
        import re
        
        # Look for patterns like "SCORE: 75" or "Score: 75/100"
        patterns = [
            r'SCORE:\s*(\d+)',
            r'Score:\s*(\d+)',
            r'(\d+)/100',
            r'(\d+)\s*out of\s*100'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                return min(100, max(0, score))
        
        # Default to neutral if no score found
        return 50
