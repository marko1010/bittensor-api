from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from app.models.stake import StakeAction
from app.models.responses import TaoDividendsResponse, SentimentResponse

from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.security import get_api_key
from app.services.bittensor import bittensor_service
from app.services.sentiment import sentiment_service
from app.tasks.celery import process_sentiment_and_stake
from app.db.mongodb import mongodb
from contextlib import asynccontextmanager
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
mongodb_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client
    mongodb_client = mongodb.get_db()
    yield
    # Shutdown
    mongodb.close()
    await sentiment_service.close()

app = FastAPI(
    title="Bittensor API",
    description="API service for querying Tao dividends and performing sentiment-based staking",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/tao_dividends", response_model=TaoDividendsResponse, response_model_exclude_none=True)
async def get_tao_dividends(
    netuid: Optional[int] = Query(None, description="Subnet ID"),
    hotkey: Optional[str] = Query(None, description="Hotkey address"),
    trade: bool = Query(False, description="Whether to trigger sentiment-based trading"),
    api_key: str = Depends(get_api_key)
):
    """
    Get Tao dividends for a specific netuid and hotkey, or all netuids if netuid is None.
    Optionally trigger sentiment-based trading.
    """
    if trade:
        if (netuid is None) != (hotkey is None):  # XOR - one is None but not both
            raise HTTPException(
                status_code=400, 
                detail=f"{('netuid' if netuid is None else 'hotkey')} is required for trading"
            )
        elif netuid is None:  # Both are None
            netuid, hotkey = settings.DEFAULT_NETUID, settings.DEFAULT_HOTKEY
        
        process_sentiment_and_stake.delay(netuid, hotkey)


    result = await bittensor_service.get_tao_dividends(netuid, hotkey)
    dividends = result["dividends"]
    response = {
        "netuid": netuid,
        "hotkey": hotkey,
        "cache_status": result["cache_status"]
    }

    if netuid is None:
        if hotkey is None:
            response["data"] = dividends
        else:
            response["data"] = {k: v[hotkey] for k, v in dividends.items()}
    else:
        if hotkey is None:
            response["data"] = dividends[str(netuid)]
        else:
            response["dividend"] = dividends[str(netuid)][hotkey]
    
    return response

@app.get("/api/v1/sentiment/{netuid}", response_model=SentimentResponse)
async def get_subnet_sentiment(
    netuid: int,
    api_key: str = Depends(get_api_key)
):
    """
    Get sentiment analysis for a specific subnet
    """
    sentiment_data = await sentiment_service.get_subnet_sentiment(netuid)
    return sentiment_data


@app.get("/api/v1/stake_history", response_model=List[StakeAction])
async def get_stake_history(
    netuid: Optional[int] = Query(None, description="Subnet ID"),
    hotkey: Optional[str] = Query(None, description="Hotkey address"), 
    limit: int = Query(100, description="Number of records to return"),
    api_key: str = Depends(get_api_key)
):
    """
    Get historical stake actions
    """
    query = {}
    if netuid:
        query["netuid"] = netuid
    if hotkey:
        query["hotkey"] = hotkey
        
    cursor = mongodb_client.stake_actions.find(query).sort("timestamp", -1).limit(limit)
    history = await cursor.to_list(length=limit)
    return [StakeAction(**record) for record in history]


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )