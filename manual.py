import pandas as pd
import yfinance as yf
from scout import get_screener_data


def perform_manual_audit():
    print("\n--- PUMP PATROL: DUAL-INPUT MODE ---")

    # User provides both identifiers to bypass AI mapping issues
    # Example: For Covidh, Screener is '534920' and Yahoo is '534920.BO'
    s_ticker = input("📂 Enter Screener.in Symbol (e.g., 534920 or SBIN): ").strip()
    y_ticker = input("📈 Enter Yahoo Finance Ticker (e.g., 534920.BO or SBIN.NS): ").strip().upper()

    # 1. FETCH MARKET DATA (Yahoo Finance)
    print(f"⏳ Fetching market volume for {y_ticker}...")
    hist = yf.download(y_ticker, period="7d", progress=False)

    if hist.empty:
        print(f"❌ Yahoo Finance failed to find {y_ticker}. Check the .NS or .BO suffix.")
        return

    # 2. FETCH DEEP FINANCIALS (Screener.in)
    print(f"⏳ Scraping financials for {s_ticker}...")
    # We pass s_ticker directly to avoid URL suffix errors
    s_data = get_screener_data(s_ticker)

    # 3. DATA INTEGRITY GATE
    if s_data['equity'] == 0 and all(x == 0 for x in s_data['pat']):
        print(f"❌ SCRAPE ERROR: Could not find data for '{s_ticker}' on Screener.")
        return

    # Average Volume Calculation
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)
    avg_vol = int(hist['Volume'].mean())

    # 4. EVIDENCE TABLE
    # --- 4. DETAILED EVIDENCE TABLE ---
    # Mapping all 12+ columns to match your database structure
    table_data = [{
        "ticker": y_ticker,
        "pat_q1": s_data['pat'][0], "pat_q2": s_data['pat'][1], "pat_q3": s_data['pat'][2],
        "cfo_q1": s_data['cfo'][0], "cfo_q2": s_data['cfo'][1], "cfo_q3": s_data['cfo'][2],
        "equity": s_data['equity'],
        "vol_1wk": avg_vol,
        "prom_q1": s_data['promoters'][0], "prom_q2": s_data['promoters'][1], "prom_q3": s_data['promoters'][2]
    }]

    df = pd.DataFrame(table_data)

    print("\n" + "=" * 40 + " DETAILED EVIDENCE AUDIT " + "=" * 40)
    # Use to_string to ensure all columns print side-by-side without wrapping
    print(df.to_string(index=False))
    print("=" * 105)
    # 5. ANALYSIS LOGIC
    h_flag = 1 if (all(x <= 0 for x in s_data['cfo']) and all(x > 0 for x in s_data['pat'])) else 0
    v_flag = 1 if (avg_vol >= (0.5 * s_data['equity'] * 1e7)) else 0
    p_flag = 1 if (s_data['promoters'][2] - s_data['promoters'][0] <= -2.0) else 0

    score = (h_flag + v_flag + p_flag) * 33.33
    verdict = "🚨 PUMP_SUSPECT" if score >= 33.33 else "✅ SAFE"

    print(f"\nSTATUS: {verdict} | Fraud Score: {score:.2f}%")
    print("-" * 50)


if __name__ == "__main__":
    while True:
        try:
            perform_manual_audit()
        except Exception as e:
            print(f"❌ Error: {e}")