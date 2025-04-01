from typing import Dict, Union, Optional
from pydantic import BaseModel

class TaoDividendsResponse(BaseModel):
    netuid: Optional[int] = None
    hotkey: Optional[str] = None 
    cache_status: str
    data: Union[Dict[str, Union[Dict[str, int], int]], int] = None
    dividend: Optional[int] = None 

class SentimentResponse(BaseModel):
    netuid: int
    tweet_count: int
    sentiment_score: float

    