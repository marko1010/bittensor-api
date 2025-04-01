import asyncio
import logging
import traceback
from celery import Celery
from app.core.config import settings
from app.services.bittensor import bittensor_service
from app.services.sentiment import sentiment_service
from app.db.mongodb import mongodb
import json
from datetime import datetime, timezone

app = Celery(
    "bittensor_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

logger = logging.getLogger(__name__)

@app.task
def process_sentiment_and_stake(netuid: int, hotkey: str):
    return asyncio.get_event_loop().run_until_complete(_process_sentiment_and_stake(netuid, hotkey))

async def _process_sentiment_and_stake(netuid: int, hotkey: str):
    """
    Process sentiment analysis and perform stake/unstake based on sentiment
    """
    try:
        logger.info(f"Processing sentiment and stake for netuid: {netuid} and hotkey: {hotkey}")
        sentiment_data = await sentiment_service.get_subnet_sentiment(netuid)
        sentiment_score = sentiment_data["sentiment_score"]
        if sentiment_score == 0:
            return {
                "success": True,
                "sentiment_data": sentiment_data,
                "action": "skip",
                "amount": 0
            }

        stake_amount = abs(sentiment_score) * 0.01

        if sentiment_score > 0:
            logger.info(f"Staking {stake_amount} TAO for netuid: {netuid} and hotkey: {hotkey}")
            result = await bittensor_service.stake_tao(stake_amount, netuid, hotkey)
            action = "stake"
        else:
            logger.info(f"Unstaking {stake_amount} TAO for netuid: {netuid} and hotkey: {hotkey}")
            result = await bittensor_service.unstake_tao(stake_amount, netuid, hotkey)
            action = "unstake"
        
        # Get MongoDB client only when needed
        mongodb_client = mongodb.get_db()
        await mongodb_client.stake_actions.insert_one({
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "action": action,
            "amount": stake_amount,
            "result": result["result"],
            "timestamp": datetime.now(timezone.utc)
        })
        
        return {
            "success": True,
            "sentiment_data": sentiment_data,
            "action": action,
            "amount": stake_amount,
            "result": result["result"]
        }
    except Exception as e:
        logger.error(f"Error in process_sentiment_and_stake: {str(e)}")
        logger.error("Stack trace:")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "error": str(e)
        }
