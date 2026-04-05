import pandas as pd
import yfinance as yf
import mysql.connector
import requests
from bs4 import BeautifulSoup
import time
import math

DB_CONFIG = {'host': '127.0.0.1', 'user': 'root', 'password': '31072006Palak', 'database': 'pumppatrol'}


def clean_for_mysql(val):
    if val is None or (isinstance(val, float) and math.isnan(val)): return 0.0
    return val


def get_screener_data(ticker):
    symbol = ticker.split('.')[0]
    url = f"https://www.screener.in/company/{symbol}/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    results = {'cfo': [0.0] * 3, 'promoters': [0.0] * 3, 'pat': [0.0] * 3, 'equity': 0.0}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. SCRAPE QUARTERLY PAT (from Quarterly Results table)
        q_section = soup.find('section', {'id': 'quarters'})
        if q_section:
            table = q_section.find('table', {'class': 'data-table'})
            for row in table.find_all('tr'):
                if "Net Profit" in row.text:
                    vals = [float(c.text.replace(',', '').strip()) for c in row.find_all('td')[1:] if c.text.strip()]
                    results['pat'] = (vals[-3:] + [0.0] * 3)[:3]

        # 2. SCRAPE CFO
        cf_section = soup.find('section', {'id': 'cash-flow'})
        if cf_section:
            table = cf_section.find('table', {'class': 'data-table'})
            for row in table.find_all('tr'):
                if "Cash from Operating Activity" in row.text:
                    vals = [float(c.text.replace(',', '').strip()) for c in row.find_all('td')[1:] if c.text.strip()]
                    results['cfo'] = (vals[-3:] + [0.0] * 3)[:3]

        # 3. SCRAPE PROMOTERS
        sh_section = soup.find('section', {'id': 'shareholding'})
        if sh_section:
            table = sh_section.find('table', {'class': 'data-table'})
            for row in table.find_all('tr'):
                if "Promoters" in row.text:
                    vals = [float(c.text.replace('%', '').strip()) for c in row.find_all('td')[1:] if c.text.strip()]
                    results['promoters'] = (vals[-3:] + [0.0] * 3)[:3]

        # 4. SCRAPE EQUITY CAPITAL (from Balance Sheet)
        bs_section = soup.find('section', {'id': 'balance-sheet'})
        if bs_section:
            table = bs_section.find('table', {'class': 'data-table'})
            for row in table.find_all('tr'):
                if "Equity Capital" in row.text:
                    vals = [float(c.text.replace(',', '').strip()) for c in row.find_all('td')[1:] if c.text.strip()]
                    results['equity'] = vals[-1] if vals else 0.0

    except Exception as e:
        print(f"⚠️ Screener scrape error for {ticker}: {e}")
    return results


def run_audit():
    try:
        conn = mysql.connector.connect(**DB_CONFIG);
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT ticker FROM signal_master")
        tickers = [row['ticker'] for row in cursor.fetchall()]

        for ticker in tickers:
            print(f"🚀 Full Hybrid Sync for {ticker}...")
            # 1. SCRAPER DATA
            s_data = get_screener_data(ticker)

            # 2. YAHOO DATA (Volume only)
            hist = yf.download(ticker, period="7d", auto_adjust=True, progress=False)
            if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
            avg_vol = int(hist['Volume'].mean()) if not hist.empty else 0

            # 3. UPSERT (Update or Insert)
            query = """
                    INSERT INTO stocks (ticker, pat_q1, pat_q2, pat_q3, cfo_q1, cfo_q2, cfo_q3,
                                        equity_capital, avg_vol_1week, promoter_q1, promoter_q2, promoter_q3, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'AUDITED') ON DUPLICATE KEY \
                    UPDATE \
                        pat_q1= \
                    VALUES (pat_q1), pat_q2= \
                    VALUES (pat_q2), pat_q3= \
                    VALUES (pat_q3), cfo_q1= \
                    VALUES (cfo_q1), cfo_q2= \
                    VALUES (cfo_q2), cfo_q3= \
                    VALUES (cfo_q3), equity_capital= \
                    VALUES (equity_capital), avg_vol_1week= \
                    VALUES (avg_vol_1week), promoter_q1= \
                    VALUES (promoter_q1), promoter_q2= \
                    VALUES (promoter_q2), promoter_q3= \
                    VALUES (promoter_q3), status='AUDITED' \
                    """
            data = (ticker, *s_data['pat'], *s_data['cfo'], s_data['equity'], avg_vol, *s_data['promoters'])
            cursor.execute(query, [clean_for_mysql(x) for x in data])
            conn.commit();
            time.sleep(1.5)
        print("✅ ALL BOXES FILLED.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_audit()