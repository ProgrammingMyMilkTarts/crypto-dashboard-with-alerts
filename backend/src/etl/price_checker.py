# backend/src/etl/price_checker.py

import logging
from datetime import datetime, timezone
from ..core.database import get_active_alerts,get_latest_prices,update_last_notified,deactivate_alert,get_db_engine
from ..models import Base


logging.basicConfig(level=logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    engine = get_db_engine()
    Base.metadata.create_all(bind=engine)

def check_price_alerts():
    logging.info("Starting price alert evaluation scan...")

    init_db()

    # 1. Fetch active alerts from database
    active_alerts = get_active_alerts()
    if not active_alerts:
        logging.info("No active alerts found.")
        return

    #Get uniqie symbols needed
    """for alert in active_alerts:
        symbols = list(set(alert['symbol']))"""
    #list comprehension
    symbols = list(set(alert['symbol'] for alert in active_alerts))


    #latest price
    latest_price_list = get_latest_prices(symbols)

    #map symbol -> price dictionary for lookup
    """for item in latest_price_list:
        price_map = {item['symbol']:item['price']}"""
    price_map = {item['symbol']: item['price'] for item in latest_price_list}
    

    if not price_map:
        logging.warning("No latest price found in database")
        return

    count = 0

    for alert in active_alerts:
        symbol = alert['symbol']
        target_price = alert['target_price']
        condition = alert['condition']  # 'above' or 'below'
        alert_id = alert['id']
        last_notified = alert.get('last_notified_at')

        if symbol not in price_map:
            continue

        current_price = price_map[symbol]
        is_triggered = False

        #check ocnfition
        if condition == 'above' and current_price>= target_price:
            is_triggered = True
        elif condition == 'below' and current_price <= target_price:
            is_triggered = True

        if is_triggered:
            if last_notified:
                if isinstance(last_notified,str):
                    last_notified_dt = datetime.fromisoformat(last_notified)
                else:
                    last_notified_dt = last_notified

                if last_notified_dt.tzinfo is None:
                    last_notified_dt = last_notified.replace(tzinfo = timezone.utc)

                now = datetime.now(timezone.utc)
                last_notified_since_hours = (now - last_notified_dt).total_seconds()/3600

                if last_notified_since_hours < 24:
                    logging.info(f'Alerts {alert_id} triggered for {symbol} at {current_price}')
                    continue

            logging.info(f"Alert triggered: {alert_id} for {symbol}")


            #need to all contifucation here


            update_last_notified(alert_id)
            count += 1

    logging.info(f"alert scan complete. {count} notifications")

if __name__ == "__main__":
    check_price_alerts()


