#AI guidance 
"""
    Pydantic model for crypto price data.
    This is what the API returns when someone requests prices.
    
    Example response:
    {
        "symbol": "BTC-USD",
        "price": 43250.50,
        "change_24h": 2.5,
        "volume": 1500000000,
        "timestamp": "2024-01-15T14:30:00Z"
    }
    doing a config
    Example: if we pass a SQLAlchemy CryptoPrice object,
     Pydantic will automatically extract the attributes
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CryptoPrice(BaseModel):
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume: Optional[float] = None
    timestamp: datetime

    class config:
        # This allows Pydantic to accept SQLAlchemy model objects
        # and convert them automatically
        from_attributes = True
