#chrypto_fetcher.py: Fetches from yfinance $\rightarrow$ Cleans $\rightarrow$ Saves to Postgres $\rightarrow$ Checks threshold & sends WhatsApp if triggered $\rightarrow$ Scheduled via crontab
import logging 
import random
import time
import pandas as pd
import requests
import yfinance as yf
from ..core.database import get_db_engine,save_crypto_price
from ..models.crypto import CryptoPrice  # Adjust to your crypto model import
import os
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker



logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
# Keep it focused on major cryptos
TARGET_TICKERS = ["BTC-USD","ETH-USD", "SOL-USD"]


#yahoo finance way but getting botted
# def run_crypto_fetcher():
#     logging.info("Starting Bitcoin ETl")

#     #sleep a random amount of seconds so i am not picked up by bots
#     for symbol in TARGET_TICKERS:
#         try:
#             time.sleep(random.uniform(1.0,5.0))

#             session = requests.Session()
#             session.headers["User-Agent"] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

#             print(f"Fetching data for {symbol}")
#             ticker = yf.Ticker(symbol,session=session)

#             df = ticker.history(period = "2d")

#             if df.empty or len(df)<1:
#                 logging.warning(f"No data is found{symbol}")
#                 continue

#             # Extract latest metrics
#             current_price = float(df['Close'].iloc[-1])
#             current_volume = float(df['Volume'].iloc[-1])

#             # Calculate 24h change if we have yesterday's data
#             change_24h = 0.0
#             if len(df)>=2:
#                 prev_price = float(df['Close'].iloc[-2])
#                 change_24h = ((current_price - prev_price) / prev_price) *100
            
#             # Save directly using your new database function
#             saved_record = save_crypto_price(
#                 symbol=symbol,
#                 price=current_price,
#                 change_24h=change_24h,
#                 volume=current_volume
#             )

#             logging.info(f"Successfully saved {symbol}: ${current_price:,.2f} ({change_24h:+.2f}%)")                

#         except Exception as e:
#             logging.error(f"ETL failed: {e}")

def fetch_and_store_prices():
    logging.info("Starting crypto price ETL via CoinGecko...")
    
    # CoinGecko free API mapping for your symbols
    # IDs correspond to CoinGecko's asset identifiers
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"

    engine = get_db_engine()
    #make session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Map API response back to your database symbols
        price_map = {
            'BTC-USD': data.get('bitcoin', {}).get('usd'),
            #'ETH-USD': data.get('ethereum', {}).get('usd'),
            #'SOL-USD': data.get('solana', {}).get('usd')
        }
        
        # Insert records into your database (example logic)
        # Your existing database insertion loop goes here using price_map...
        for symbol, price in price_map.items():
            if price is not None:
                logging.info(f"Fetched {symbol}: ${price}")

                #new record
                new_record = CryptoPrice(
                    symbol=symbol,
                    price=price,
                    timestamp= datetime.now()
                )
                
                session.add(new_record)
                # Save to database using your SQLAlchemy session / models
            else:
                logging.warning(f"No price returned for {symbol}")
        session.commit()
        logging.info("Success comit crypto price")   
    except Exception as e:
        session.rollback()
        logging.error(f"Failed to fetch prices from CoinGecko: {e}")


if __name__ == "__main__":
    #run_crypto_fetcher()
    fetch_and_store_prices()
