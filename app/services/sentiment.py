from typing import List, Dict, Literal
import logging
import httpx
from app.core.config import settings

class SentimentService:
    def __init__(self):
        self.http_client = httpx.AsyncClient()
        self._logger = logging.getLogger(__name__)

    async def search_tweets(self, query: str, max_results: int = 10, sort: Literal["Latest", "Top"] = "Latest") -> List[Dict]:
        """
        Search for tweets using Datura.ai API
        """
        response = await self.http_client.post(
            "https://apis.datura.ai/twitter",
            headers={
                "Authorization": settings.DATURA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "count": max_results,
                "sort": sort
            },
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0)
        )
        response.raise_for_status()
        return response.json()

    async def get_subnet_sentiment(self, netuid: int) -> Dict:
        """
        Get sentiment analysis for tweets about a specific subnet
        """
        query = f"Bittensor netuid {netuid}"
        tweets = await self.search_tweets(query)
        
        if not tweets:
            return {
                "netuid": netuid,
                "tweet_count": 0,
                "sentiment_score": 0
            }
        
        tweet_texts = [tweet.get("text", "").replace("\n", " ") for tweet in tweets]
        sentiment_score = await self._analyze_sentiment(tweet_texts)
        
        return {
            "netuid": netuid,
            "tweet_count": len(tweets),
            "sentiment_score": sentiment_score
        }

    async def _analyze_sentiment(self, tweets: List[str]) -> float:
        """
        Analyze sentiment using Chutes.ai API
        """

        tweets = "\n".join(tweets)
        prompt = f"""
        "Analyze the sentiment of these tweets about Bittensor. Return a score between -100 and +100, where -100 is extremely negative and +100 is extremely positive. Return only a single overall score without any other text or explanations."

        Tweets:
        {tweets}
        """
        
        response = await self.http_client.post(
            "https://llm.chutes.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.CHUTES_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "unsloth/Llama-3.2-3B-Instruct",
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            },
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0)
        )
        response.raise_for_status()
        result = response.json()
        return float(result["choices"][0]["message"]["content"])

    async def close(self):
        await self.http_client.aclose()

sentiment_service = SentimentService() 