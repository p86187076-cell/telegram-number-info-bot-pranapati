#!/usr/bin/env python3
"""
Telegram Number Info Bot
A complete Telegram bot for fetching mobile number information from an API.
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional, Any

import requests
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ===================================================
# CONFIGURATION
# ===================================================
BOT_TOKEN = "8574337060:AAE8IzX3pExvA0kYpSXcp3IMP9-zgRRv37k"
API_URL = "https://ansh-apis.is-dev.org/api/creta?key=ansh&num="

# ===================================================
# LOGGING SETUP
# ===================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================================================
# BOT INITIALIZATION
# ===================================================
try:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    bot.get_me()
    logger.info("✅ Bot connected successfully!")
except Exception as e:
    logger.error(f"❌ Bot initialization failed: {e}")
    exit(1)

# ===================================================
# KEYBOARD FUNCTIONS
# ===================================================
def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        row_width=1
    )
    btn_get_info = KeyboardButton("🔍 Get Info")
    keyboard.add(btn_get_info)
    return keyboard

# ===================================================
# UTILITY FUNCTIONS
# ===================================================
def is_valid_mobile_number(number: str) -> bool:
    number = number.strip()
    return bool(re.match(r'^\d{10}$', number))

def format_record(record: Dict[str, Any], index: int) -> str:
    """
    Format a single record into a beautiful message.
    Handles the new API response format.
    """
    mobile = record.get("mobile", "Not Available")
    name = record.get("name", "Not Available")
    fname = record.get("fname", "Not Available")
    address = record.get("address", "Not Available")
    alt = record.get("alt", "Not Available")
    circle = record.get("circle", "Not Available")
    record_id = record.get("id", "Not Available")
    email = record.get("email", "Not Available")

    # Clean up address - replace ! with newlines for better readability
    if address != "Not Available":
        address = address.replace("!", "\n")

    message = f"""
╭━━━〔 📱 NUMBER INFO {index+1} 〕━━━⬣

👤 <b>Name</b>        : {name}
👨 <b>Father</b>      : {fname}
📞 <b>Mobile</b>      : {mobile}
📱 <b>Alternate</b>   : {alt}
📡 <b>Circle</b>      : {circle}
🆔 <b>ID</b>          : {record_id}
📧 <b>Email</b>       : {email if email else "Not Available"}

🏠 <b>Address</b> :
{address}

━━━━━━━━━━━━━━━━━━━━"""
    return message.strip()

def format_no_data(number: str) -> str:
    return f"""
╭━━━〔 ❌ NO DATA FOUND 〕━━━⬣

📞 Number : {number}

⚠️ Is Number Ka Koi Data Nahi Hai.

Please Try Another Number.

╰━━━━━━━━━━━━━━━━━━⬣"""

def fetch_number_info(number: str) -> Optional[Dict[str, Any]]:
    """
    Fetch number information from the API.
    Returns the JSON response as dictionary or None on error.
    """
    try:
        url = f"{API_URL}{number}"
        logger.info(f"Calling API: {url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Response Status Code: {response.status_code}")

        if response.status_code == 404:
            logger.warning(f"Number {number} not found (404)")
            return {"Results": []}

        response.raise_for_status()
        data = response.json()
        logger.info(f"API Response received successfully")

        return data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout error while fetching number {number}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while fetching number {number}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e} while fetching number {number}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

def handle_number_lookup(message: Message, number: str) -> None:
    chat_id = message.chat.id

    searching_msg = bot.send_message(chat_id, "🔍 Searching Information...")

    data = fetch_number_info(number)

    if data is None:
        bot.edit_message_text(
            "⚠️ Server Error.\n\nPlease Try Again Later.",
            chat_id,
            searching_msg.message_id
        )
        return

    # Extract records from the new API format
    records = data.get("Results", [])

    if not records or not isinstance(records, list):
        no_data_msg = format_no_data(number)
        bot.edit_message_text(no_data_msg, chat_id, searching_msg.message_id)
        return

    total_records = len(records)

    # Delete the searching message
    bot.delete_message(chat_id, searching_msg.message_id)

    # Send each record as a separate message
    for idx, record in enumerate(records):
        formatted_record = format_record(record, idx)
        bot.send_message(chat_id, formatted_record, parse_mode="HTML")

    # Send total records count
    bot.send_message(chat_id, f"📊 Total Records Found : {total_records}")

# ===================================================
# BOT HANDLERS
# ===================================================
@bot.message_handler(commands=['start'])
def handle_start(message: Message) -> None:
    chat_id = message.chat.id
    welcome_message = """
🌟 <b>Welcome to Number Info Bot!</b>

Get detailed information about any Indian mobile number instantly.

Simply press the button below to get started.

━━━━━━━━━━━━━━━━━━━
<b>📌 How it works:</b>
1️⃣ Press <code>🔍 Get Info</code>
2️⃣ Send any 10-digit mobile number
3️⃣ Get detailed information
"""

    bot.send_message(
        chat_id,
        welcome_message,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: message.text == "🔍 Get Info")
def handle_get_info(message: Message) -> None:
    chat_id = message.chat.id

    info_message = """
📱 <b>Please Send Mobile Number</b>

Example:
<code>1234567890</code>

✅ Send Any Valid 10 Digit Mobile Number.
"""

    bot.send_message(
        chat_id,
        info_message,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@bot.message_handler(content_types=['text'])
def handle_text_messages(message: Message) -> None:
    chat_id = message.chat.id
    user_input = message.text.strip()

    if user_input.startswith('/'):
        return

    if is_valid_mobile_number(user_input):
        handle_number_lookup(message, user_input)
    else:
        error_message = """
❌ <b>Invalid Mobile Number.</b>

Please send a valid 10-digit mobile number.
Example: <code>1234567890</code>
"""

        bot.send_message(
            chat_id,
            error_message,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )

# ===================================================
# POLLING WITH ERROR HANDLING
# ===================================================
def run_bot() -> None:
    logger.info("Starting Number Info Bot...")
    logger.info(f"Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"API URL: {API_URL}")

    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=1, timeout=60)
        except telebot.apihelper.ApiTelegramException as e:
            if "409" in str(e):
                logger.warning("Conflict error - webhook removed, retrying...")
                bot.remove_webhook()
                time.sleep(2)
            elif "404" in str(e):
                logger.error("❌ INVALID BOT TOKEN!")
                break
            else:
                logger.error(f"Telegram API error: {e}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
