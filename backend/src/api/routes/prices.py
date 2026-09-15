from fastapi import APIRouter, HTTPException

from core.database import get_latest_prices

router = APIRouter(prefix="/api/prices", tags=["Prices"])


@router.get("/")
def get_prices(symbol: str = "BTC-USD,ETH-USD,SOL-USD"):
    symbol_list = [s.strip() for s in symbol.split(",") if s.strip()]

    try:
        prices = get_latest_prices(symbol_list)
        return {"Success": True, "data": prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))