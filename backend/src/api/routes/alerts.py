from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
import secrets

from core.database import get_db_engine

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


class AlertCreateRequest(BaseModel):
    # This model defines the payload required to create an alert.
    # The contact can be an email address or a WhatsApp number depending on the app flow.
    symbol: str
    target_price: float
    condition: str
    notification_method: str
    contact: str


@router.post("/")
def create_alert(payload: AlertCreateRequest):
    # Create a new alert and return a one-time unsubscribe token.
    # The token is generated before insertion so the user can cancel the alert later
    # without exposing the database id in the public API.
    try:
        token = secrets.token_urlsafe(32)
        engine = get_db_engine()

        with engine.begin() as conn:
            query = text("""
                INSERT INTO alerts (
                    symbol,
                    target_price,
                    condition,
                    notification_method,
                    contact,
                    unsubscribe_token,
                    is_active
                )
                VALUES (
                    :symbol,
                    :target_price,
                    :condition,
                    :method,
                    :contact,
                    :token,
                    TRUE
                )
                RETURNING id;
            """)

            result = conn.execute(
                query,
                {
                    "symbol": payload.symbol,
                    "target_price": payload.target_price,
                    "condition": payload.condition,
                    "method": payload.notification_method,
                    "contact": payload.contact,
                    "token": token,
                },
            )
            alert_id = result.fetchone()[0]

        return {
            "success": True,
            "message": "Alert created",
            "alert_id": alert_id,
            "unsubscribe_token": token,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create alert: {str(e)}")


@router.delete("/unsubscribe/{token}")
def unsubscribe_alert(token: str):
    # Delete the alert when a user unsubscribes using the secret token.
    # This is safer than accepting a numeric id because the token is random and harder to guess.
    try:
        engine = get_db_engine()
        with engine.begin() as conn:
            query = text("DELETE FROM alerts WHERE unsubscribe_token = :token RETURNING id;")
            result = conn.execute(query, {"token": token}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Invalid unsubscribe token")

        return {"success": True, "message": "Successfully unsubscribed from alerts."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not unsubscribe alert: {str(e)}")
