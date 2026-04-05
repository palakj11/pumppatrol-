from datetime import datetime

from flask import Flask, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
import os
import json
import time
import evidence_gen  # Imports the new email function
import smtplib

# --- 1. SETUP PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

print("--------------------------------------------------")
print("🔎 SEARCHING FOR 'index.html'...")
final_template_folder = BASE_DIR
if os.path.exists(os.path.join(TEMPLATES_DIR, 'index.html')):
    final_template_folder = TEMPLATES_DIR
elif os.path.exists(os.path.join(BASE_DIR, 'index.html')):
    final_template_folder = BASE_DIR
print("--------------------------------------------------")

app = Flask(__name__, template_folder=final_template_folder, static_folder=BASE_DIR)
CORS(app)

# File Paths
CSV_FILE = os.path.join(BASE_DIR, 'data', 'telegram_log.csv')
JSON_FILE = os.path.join(BASE_DIR, 'data', 'dashboard_data.json')
LOOKER_FILE = os.path.join(BASE_DIR, 'data', 'looker_feed.csv')


@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>Startup Error</h1><p>{e}</p>"


@app.route('/api/live_data')
def get_live_data():
    messages = []
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            df = df.iloc[::-1].head(20)
            messages = df.to_dict(orient='records')
        except:
            pass

    analysis = {"hype_score": 10, "status": "SAFE", "price": "Rs 7.45", "options_watch": "None", "admin_id": "Unknown"}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r') as f:
                analysis = json.load(f)
        except:
            pass

    return jsonify({"messages": messages, "analysis": analysis})


@app.route('/api/looker_download')
def download_looker_data():
    if os.path.exists(LOOKER_FILE):
        return send_file(LOOKER_FILE, as_attachment=True)
    return jsonify({"error": "No data yet"}), 404


@app.route('/api/trigger_cyber_cell')
def trigger_cyber_cell():
    """
    Generates Evidence PDF and Emails it to the Cyber Cell.
    """
    print("\n" + "=" * 50)
    print("👮 CYBER CELL PROTOCOL INITIATED")

    # 1. Gather Data for Report
    messages = []
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            messages = df.iloc[::-1].head(15).to_dict(orient='records')
        except:
            pass

    analysis = {}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r') as f:
                analysis = json.load(f)
        except:
            pass

    scam_data = {
        "stock": f"VODAFONE IDEA (VI) | Opt: {analysis.get('options_watch', 'None')}",
        "status": analysis.get('status', 'CRITICAL'),
        "score": analysis.get('hype_score', 0),
        "messages": messages
    }

    # 2. Generate PDF & Email
    try:
        pdf_path = evidence_gen.generate_pdf(scam_data)
        success = evidence_gen.send_email_report(pdf_path, "sawantkedar0803@gmail.com")

        status_msg = "Report Sent" if success else "Email Failed"
        print(f"🚨 STATUS: {status_msg}")
        print("=" * 50 + "\n")

        return jsonify({
            "status": status_msg,
            "recipient": "sawantkedar0803@gmail.com",
            "time": datetime.datetime.now().strftime("%I:%M %p")
        })
    except Exception as e:
        print(f"❌ SERVER ERROR: {e}")
        return jsonify({"status": "Error", "error": str(e)}), 500


@app.route('/api/generate_report')
def create_legal_report():
    # Similar logic for manual download
    messages = []
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            messages = df.iloc[::-1].head(15).to_dict(orient='records')
        except:
            pass

    analysis = {}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r') as f:
                analysis = json.load(f)
        except:
            pass

    scam_data = {
        "stock": f"VODAFONE IDEA (VI) | Opt: {analysis.get('options_watch', 'None')}",
        "status": analysis.get('status', 'CRITICAL'),
        "score": analysis.get('hype_score', 0),
        "messages": messages
    }

    try:
        pdf_path = evidence_gen.generate_pdf(scam_data)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 DASHBOARD ONLINE: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)