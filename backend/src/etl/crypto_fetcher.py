#chrypto_fetcher.py: Fetches from yfinance $\rightarrow$ Cleans $\rightarrow$ Saves to Postgres $\rightarrow$ Checks threshold & sends WhatsApp if triggered $\rightarrow$ Scheduled via crontab
import logging 
import requests
from ..core.database import save_crypto_price



logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

COINGECKO_IDS = {
    "BTC-USD": "bitcoin",
    "ETH-USD": "ethereum",
    "SOL-USD": "solana",
}


def build_price_map(data):
    """Translate CoinGecko asset IDs into symbols and include 24h change and volume."""
    price_map = {}
    
    mapping = {
        "BTC-USD": "bitcoin",
        "ETH-USD": "ethereum",
        "SOL-USD": "solana",
    }
    
    for symbol, coingecko_id in mapping.items():
        coin_data = data.get(coingecko_id, {})
        price_map[symbol] = {
            "price": coin_data.get("usd"),
            "change_24h": coin_data.get("usd_24h_change"),
            "volume": coin_data.get("usd_24h_vol"),
        }
        
    return price_map

def fetch_and_store_prices():
    logging.info("Starting crypto price ETL via CoinGecko...")
    
    # CoinGecko free API mapping for your symbols
    # IDs correspond to CoinGecko's asset identifiers
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum,solana"
        "&vs_currencies=usd"
        "&include_24hr_change=true"
        "&include_24hr_vol=true"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    price_map = build_price_map(response.json())

    saved_count = 0
    for symbol, metrics in price_map.items():
        price = metrics.get("price")
        if price is None:
            logging.warning("No price returned for %s", symbol)
            continue

        save_crypto_price(
            symbol=symbol, 
            price=float(price),
            change_24h= metrics.get("change_24h"),
            volume= metrics.get("volume"))
        saved_count += 1
        logging.info("Saved %s: $%s", symbol, price)

    logging.info("Successfully saved %d crypto prices", saved_count)

if __name__ == "__main__":
    #run_crypto_fetcher()
    fetch_and_store_prices()
