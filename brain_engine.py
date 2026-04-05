import mysql.connector
import time
import re
import yfinance as yf


# --- DATABASE CONFIG ---
DB_CONFIG = {
    'host': '127.0.0.1', 'user': 'root',
    'password': '31072006Palak', 'database': 'pumppatrol'
}


def ticker_exists(ticker_ns):
    """Fast check to see if ticker exists on Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker_ns)
        # Accessing fast_info is quicker and triggers a 404 if invalid
        if stock.fast_info['lastPrice'] > 0:
            return True
        return False
    except:
        return False


def analyze_and_clean_signals():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # FETCH: Only 'Pending' logs
        cursor.execute("SELECT id, message_text FROM Telegram_Log WHERE processing_status = 'Pending'")
        messages = cursor.fetchall()

        for msg in messages:
            text = msg['message_text']

            # Refined Regex: Looks for 3-10 capital letters
            # Blacklist common false positives found in your logs
            potential_tickers = re.findall(r'\b[A-Z]{3,10}\b', text)
            blacklist = ['BUY', 'SELL', 'TARGET', 'STILL', 'CLICK', 'PAID', 'EQUITY',
                         'STOCK', 'OPTIONS', 'ABOVE', 'INDIAN', 'MARKET', 'TODAY']

            for raw_ticker in potential_tickers:
                if raw_ticker in blacklist: continue

                ticker_ns = f"{raw_ticker}.NS"

                # --- NEW LOGIC: ONLY CHECK IF EXISTS ---
                if ticker_exists(ticker_ns):
                    # Step 1: Add to Signal Master
                    insert_query = """INSERT \
                    IGNORE INTO Signal_Master (log_id, ticker, segment, action)
                                   VALUES ( \
                    %s, \
                    %s, \
                    'Delivery', \
                    'BUY' \
                    )"""
                    cursor.execute(insert_query, (msg['id'], ticker_ns))

                    # Step 2: Initialize in Stocks table for Scout Engine to find
                    init_stock_query = "INSERT IGNORE INTO stocks (ticker, status) VALUES (%s, 'PENDING_SCOUT')"
                    cursor.execute(init_stock_query, (ticker_ns,))

                    conn.commit()
                    print(f"📡 TICKER DETECTED & PROMOTED: {ticker_ns}")

            # Mark log as Done regardless of whether a ticker was found
            cursor.execute("UPDATE Telegram_Log SET processing_status = 'Done' WHERE id = %s", (msg['id'],))
            conn.commit()

        cursor.close();
        conn.close()
    except Exception as e:
        print(f"❌ Brain Engine Error: {e}")


if __name__ == "__main__":
    print("🚀 BRAIN ENGINE: TICKER DISCOVERY MODE ACTIVE...")
    while True:
        analyze_and_clean_signals()
        time.sleep(5)