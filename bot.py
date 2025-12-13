import telebot
import os
import requests
import json
from datetime import datetime
from flask import Flask, request

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8480622059:AAHKRrUQK6Gw0ACZLiBLYwc9Cf9laodogVM")
AUTHOR = os.getenv("AUTHOR", "@FAHIM0200")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Flask app
app = Flask(__name__)

# Simple command handler
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    bot.reply_to(message, f"🤖 *Bot is online!*\nAuthor: {AUTHOR}\n\nSend `/p CARD|MONTH|YEAR|CVV`", parse_mode='Markdown')

@bot.message_handler(commands=['ping', 'test'])
def ping_command(message):
    bot.reply_to(message, "✅ *Bot is running!*", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    
    # Handle .p and /p commands
    if text.startswith(('.p ', '.P ', '/p ', '/P ')):
        card_details = text[3:].strip()
        
        if '|' not in card_details or len(card_details.split('|')) != 4:
            bot.reply_to(message, "❌ Invalid format. Use: `/p 4242424242424242|01|26|000`", parse_mode='Markdown')
            return
        
        # Simple processing (you'll add your API calls here later)
        username = f"@{message.from_user.username}" if message.from_user.username else "User"
        
        result = f"""✅ *TEST RESPONSE*

*Card:* `{card_details}`
*Status:* Test successful
*User:* {username}
*Author:* {AUTHOR}
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━"""
        
        bot.reply_to(message, result, parse_mode='Markdown')

# Webhook for Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

@app.route('/')
def home():
    return f"""
    <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1>🤖 Card Processor Bot</h1>
            <p><strong>Status:</strong> ✅ Online</p>
            <p><strong>Author:</strong> {AUTHOR}</p>
            <p>Bot is running on Render!</p>
        </body>
    </html>
    """

if __name__ == '__main__':
    print("🤖 Bot starting...")
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
