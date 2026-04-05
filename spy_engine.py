import os
import datetime
import mysql.connector
from telethon import TelegramClient, events
from dotenv import load_dotenv

load_dotenv()
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE_NUMBER')
session_name = 'pump_patrol_session'
# Database Configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '31072006Palak',
    'database': 'pumppatrol'
}


def save_to_db(timestamp, sender_id, group_name, text):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = "INSERT INTO telegram_Log (timestamp, sender_id, group_name, message_text) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (timestamp, str(sender_id), str(group_name), text))

        # --- MISSING LINE BELOW ---
        conn.commit()
        # --------------------------

        cursor.close()
        conn.close()
        print(f"✅ Hard-Saved to SQL: {text[:20]}...")
    except Exception as e:
        print(f"❌ DB Error: {e}") # This will tell you if the column type is wrong


client = TelegramClient('pump_patrol_session', os.getenv('API_ID'), os.getenv('API_HASH'))


async def backfill_one_week():
    print("⏳ BACKFILLING 1 WEEK OF HISTORY...")
    # Use timezone-aware datetime to match Telegram's API
    seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

    # Use the group entity instead of a raw link for better reliability
    groups = ['https://t.me/+sosvM755kpJlNzI9'] # Or the specific username

    for group in groups:
        try:
            entity = await client.get_entity(group)
            async for message in client.iter_messages(entity, offset_date=seven_days_ago, reverse=True):
                if message.text:
                    save_to_db(message.date, message.sender_id, entity.title, message.text)
        except Exception as e:
            print(f"⚠️ Error accessing group {group}: {e}")
    print("✅ BACKFILL COMPLETE.")


@client.on(events.NewMessage)
async def my_event_handler(event):
    sender = await event.get_sender()
    chat = await event.get_chat()
    sender_id = sender.id if sender else "Unknown"
    chat_title = chat.title if hasattr(chat, 'title') else "Private"

    save_to_db(datetime.datetime.now(), sender_id, chat_title, event.text)
    print(f"📡 Intercepted: {chat_title}")


with client:
    client.loop.run_until_complete(backfill_one_week())
    print("🚀 LISTENING LIVE...")
    client.run_until_disconnected()