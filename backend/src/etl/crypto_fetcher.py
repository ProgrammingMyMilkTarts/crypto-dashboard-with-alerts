#chrypto_fetcher.py: Fetches from yfinance $\rightarrow$ Cleans $\rightarrow$ Saves to Postgres $\rightarrow$ Checks threshold & sends WhatsApp if triggered $\rightarrow$ Scheduled via crontab
import logging 
import random
import time
import pandas as pd
import requests
import yfinance as yf
from ..core.database import get_db_engine,save_crypto_price
import os


logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
# Keep it focused on major cryptos
TARGET_TICKERS = ["BTC-USD"]
#, "ETH-USD", "SOL-USD"

def run_crypto_fetcher():
    logging.info("Starting Bitcoin ETl")

    #sleep a random amount of seconds so i am not picked up by bots
    
    for symbol in TARGET_TICKERS:
        try:
            time.sleep(random.uniform(1.0,5.0))

            session = requests.Session()
            session.headers["User-Agent"] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

            print(f"Fetching data for {symbol}")
            ticker = yf.Ticker(symbol,session=session)

            df = ticker.history(period = "2d")

            if df.empty or len(df)<1:
                logging.warning(f"No data is found{symbol}")
                continue

            # Extract latest metrics
            current_price = float(df['Close'].iloc[-1])
            current_volume = float(df['Volume'].iloc[-1])

            # Calculate 24h change if we have yesterday's data
            change_24h = 0.0
            if len(df)>=2:
                prev_price = float(df['Close'].iloc[-2])
                change_24h = ((current_price - prev_price) / prev_price) *100
            
            # Save directly using your new database function
            saved_record = save_crypto_price(
                symbol=symbol,
                price=current_price,
                change_24h=change_24h,
                volume=current_volume
            )

            logging.info(f"Successfully saved {symbol}: ${current_price:,.2f} ({change_24h:+.2f}%)")                

        except Exception as e:
            logging.error(f"ETL failed: {e}")

if __name__ == "__main__":
    run_crypto_fetcher()
