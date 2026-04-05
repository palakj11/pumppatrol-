import mysql.connector

DB_CONFIG = {
    'host': '127.0.0.1', 'user': 'root',
    'password': '31072006Palak', 'database': 'pumppatrol'
}


def run_analysis():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM stocks")
        stocks = cursor.fetchall()

        for s in stocks:
            ticker = s['ticker']

            # --- Convert Decimal/None types to Float safely ---
            cfo_vals = [float(s[f'cfo_q{i}'] or 0) for i in range(1, 4)]
            pat_vals = [float(s[f'pat_q{i}'] or 0) for i in range(1, 4)]
            prom_vals = [float(s[f'promoter_q{i}'] or 0) for i in range(1, 4)]
            equity = float(s['equity_capital'] or 0)
            vol = float(s['avg_vol_1week'] or 0)

            # --- PILLAR 1: HOLLOW PAT ---
            # Flag if ALL 3 quarters: CFO <= 0 and PAT > 0
            h_flag = 1 if (all(x <= 0 for x in cfo_vals) and all(x > 0 for x in pat_vals)) else 0

            # --- PILLAR 2: VOLUME SPIKE ---
            # Flag if 1-week avg volume >= 50% of Equity Capital (in Cr)
            v_flag = 1 if (vol >= (0.5 * equity * 1e7)) else 0

            # --- PILLAR 3: PROMOTER EXIT ---
            # Flag if decrease from Q1 to Q3 is >= 2%
            # (Note: Q3 is latest, Q1 is oldest in your logic)
            p_flag = 1 if (prom_vals[2] - prom_vals[0] <= -2.0) else 0

            # --- FINAL WEIGHTED SCORING ---
            score = (h_flag + v_flag + p_flag) * 33.33
            status = "PUMP_SUSPECT" if score >= 33.33 else "SAFE"

            update_query = """
                           UPDATE stocks \
                           SET hollow_flag        = %s, \
                               vol_equity_flag    = %s, \
                               promoter_exit_flag = %s, \
                               fraud_score        = %s, \
                               status             = %s
                           WHERE ticker = %s \
                           """
            cursor.execute(update_query, (h_flag, v_flag, p_flag, score, status, ticker))

        conn.commit()
        print("✅ Analysis Complete: Data types handled and scores updated.")

    except Exception as e:
        print(f"❌ Analysis Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close();
            conn.close()


if __name__ == "__main__":
    run_analysis()