import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio

load_dotenv()
bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

async def send(message):
    if CHAT_ID:
        await bot.send_message(chat_id=CHAT_ID, text=f"Pyth Z-Bot: {message}")
    else:
        print(f"[ALERT] {message}")
