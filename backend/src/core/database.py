#database.py connect to postgres

import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from dotenv import load_dotenv
from typing import List,Dict,Optional
import secrets

load_dotenv(override = True)

#databae connection
def get_db_engine():
    # 1. Check if a single full DATABASE_URL is provided 
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return create_engine(database_url)

    #2 if not go back to local
    # Grab secrets securely from environment variables
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME', 'financial_db')

    # Create and return the SQLAlchemy engine connection object
    engine = create_engine(
        f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'
    )
    return engine

#Setup
Base = declarative_base()
engine = get_db_engine()
sessionlocal = sessionmaker(autocommit = False,autoflush=False,bind=engine)

#SQLAlchemy Models
#CryptoPrice
class CryptoPrice(Base):
    #Represents the crypto_prices table in postgresSQL
    __tablename__ = 'crypto_prices'

    id=Column(Integer,primary_key=True,index=True)
    symbol = Column(String(20),nullable=False,index=True)
    price = Column(Float,nullable=False)
    change_24h = Column(Float,nullable=False)
    volume = Column(Float,nullable=False)
    timestamp = Column(DateTime,server_default=func.now(),index=True)

    def to_dict(self):
        #converting model to dic
        return{
        "symbol": self.symbol,
        "price": self.price,
        "change_24h": self.change_24h,
        "volume": self.volume,
        "timstamp": self.timestamp.isoformat() if self.timestamp else None
        }

##Alerts
class Alert(Base):
    #Alerts table in PostgreSql
    __tablename__ = "alerts"

    #columns
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)

    #alert type
    alert_type = Column(String(20), nullable=False,default='price')

    target_price = Column(Float, nullable=False)
    condition = Column(String(10), nullable=False)  # 'above' or 'below'

    #percentage change alerts
    target_percent = Column(Float,nullable=True)
    percent_condition = Column(String(10),nullable=True)
    percent_timeframe = Column(String(10),nullable=True)

    #For drop alerts
    drop_percent = Column(Float,nullable=True)
    lookback_days = Column(Integer,nullable=True)

    #For volume alerts
    target_volume = Column(Float, nullable=True)
    volume_condition = Column(String(10), nullable=True)

    #contact info
    contact = Column(String(255), nullable=False)
    notification_method = Column(String(20), nullable=False)  # 'email' or 'whatsapp'

    #tracking
    unsubscribe_token = Column(String(64),unique=True,nullable=False)
    is_active = Column(Boolean,default=True,index=True)
    created_at = Column(DateTime,nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    last_notified_at = Column(DateTime, nullable=True)

    #tracking for historical data
    triggered_count = Column(Integer, default=0)
    last_trigger_price = Column(Float, nullable=True)

    def to_dict(self):
        #convert model to dictionary
        return {
            "id": self.id,
            "symbol": self.symbol,
            "alert_type": self.alert_type,
            "target_price": self.target_price,
            "condition": self.condition,
            "target_percent": self.target_percent,
            "percent_condition": self.percent_condition,
            "drop_percent": self.drop_percent,
            "target_volume": self.target_volume,
            "contact": self.contact,
            "notification_method": self.notification_method,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "triggered_count": self.triggered_count,
            "last_trigger_price": self.last_trigger_price,
            "unsubscribe_token": self.unsubscribe_token
        }

#init
def init_db():
    engine = get_db_engine()
    Base.metadata.create_all(bind = engine)
    print("Tables created/verified")

#session
#Used by FastAPI: async def endpoint(db: Session = Depends(get_db))
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


def save_crypto_price(symbol: str, price: float, change_24h: Float = None, volume: Float = None):
    #Save a crypto price to database
    db = sessionlocal()

    try:
        price_record = CryptoPrice(
            symbol=symbol,
            price = price,
            change_24h = change_24h,
            volume=volume
            )
        db.add(price_record)
        db.commit()
        db.refresh(price_record)
        return price_record.to_dict()
    finally:
        db.close()

def get_latest_prices(symbols: List[str]) -> List[Dict]:
    db = sessionlocal()
    try:
        subquery = db.query(
            CryptoPrice.symbol,
            func.max(CryptoPrice.timestamp).label('max_timestamp')
        ).filter(CryptoPrice.symbol.in_(symbols))\
         .group_by(CryptoPrice.symbol)\
         .subquery()
        
        results = db.query(CryptoPrice).join(subquery,
            (CryptoPrice.symbol == subquery.c.symbol) & 
            (CryptoPrice.timestamp == subquery.c.max_timestamp)
        ).all()
        
        return [r.to_dict() for r in results]
    finally:
        db.close()

def create_alert(alert_data: dict) -> int:
    db = sessionlocal()
    try:
        token = secrets.token_urlsafe(32)
        
        alert = Alert(
            symbol=alert_data['symbol'],
            target_price=alert_data['target_price'],
            condition=alert_data['condition'],
            contact=alert_data['contact'],
            notification_method=alert_data['notification_method'],
            unsubscribe_token=token,
            is_active=True
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert.id
    finally:
        db.close()

def get_active_alerts() -> List[Dict]:
    #Get alerts that are currently active
    db = sessionlocal()
    try:
        alerts = db.query(Alert).filter(Alert.is_active == True).all()
        return [a.to_dict() for a in alerts]
    finally:
        db.close()

def deactivate_alert(alert_id: int) -> bool:
    #deactivate an alert
    db = sessionlocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_active = False
            alert.deactivated_at = func.now()
            db.commit()
            return True
        return False
    finally:
        db.close()

#find an alert by its unsub token
def get_alert_by_token(token: str) -> Optional[Dict]:
    db = sessionlocal()
    try:
        alert = db.query(Alert).filter(Alert.unsubscribe_token == token).first()
        return alert.to_dict() if alert else None
    finally:
        db.close()

#updates the last notified timestamp to make sure we dont spam user
def update_last_notified(alert_id: int) -> bool:
    db = sessionlocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.last_notified_at = func.now()
            db.commit()
            return True
        return False
    finally:
        db.close()