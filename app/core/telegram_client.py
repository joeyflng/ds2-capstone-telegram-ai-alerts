"""
Telegram client module for sending messages and media
"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(message: str):
    """Send text message to Telegram chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # First try with Markdown
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Message sent:", response.json())
        return response.json()
    except requests.exceptions.HTTPError as e:
        # If Markdown parsing fails, try without parse_mode
        if "400" in str(e):
            print(f"⚠️ Markdown parsing failed, trying plain text...")
            print(f"⚠️ Original message length: {len(message)}")
            print(f"⚠️ Message preview: {message[:200]}...")
            
            payload_plain = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            }
            
            try:
                response = requests.post(url, data=payload_plain)
                response.raise_for_status()
                print("Message sent (plain text):", response.json())
                return response.json()
            except Exception as plain_error:
                print(f"❌ Plain text also failed: {plain_error}")
                # Try with shortened message
                short_message = message[:4000] if len(message) > 4000 else message
                payload_short = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": f"⚠️ Message formatting error. Shortened message:\n\n{short_message}"
                }
                response = requests.post(url, data=payload_short)
                return response.json()
        else:
            raise e


def send_telegram_photo(image_path: str, caption: str = ""):
    """Send image to Telegram chat"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            print(f"📸 Image sent: {response.json()}")
            return True
    except Exception as e:
        print(f"❌ Error sending photo: {e}")
        return False


def get_telegram_updates(offset: int = 0):
    """Get new messages from Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    payload = {
        "offset": offset,
        "timeout": 10,
        "allowed_updates": ["message"]
    }
    
    try:
        response = requests.get(url, params=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return None


def delete_telegram_message(message_id: int):
    """Delete a specific message from Telegram chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id
    }
    
    try:
        response = requests.post(url, data=payload, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def clear_chat_history(max_messages: int = 50):
    """Clear recent chat history by deleting bot messages"""
    print("🧹 Clearing chat history...")
    
    try:
        # Get recent updates to find message IDs
        updates = get_telegram_updates()
        if not updates or 'result' not in updates or not updates['result']:
            print("ℹ️ No recent messages found to clear")
            return
            
        # Get the most recent message ID to work backwards from
        latest_update = max(updates['result'], key=lambda x: x.get('update_id', 0))
        if 'message' not in latest_update:
            print("ℹ️ No messages found in updates")
            return
            
        latest_message_id = latest_update['message']['message_id']
        deleted_count = 0
        
        # Try to delete recent messages (working backwards)
        # Silently handle errors since old messages may not be deletable
        for i in range(max_messages):
            message_id = latest_message_id - i
            if message_id <= 0:
                break
                
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
                payload = {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id}
                response = requests.post(url, data=payload, timeout=5)
                
                if response.status_code == 200:
                    deleted_count += 1
                # Silently skip 400 errors (message too old, already deleted, etc.)
                
            except Exception:
                # Silently continue - message might be too old or not deletable
                continue
        
        if deleted_count > 0:
            print(f"✅ Cleared {deleted_count} messages from chat history")
        else:
            print("ℹ️ Chat history clear completed (no deletable messages found)")
            
    except Exception as e:
        print(f"⚠️ Chat history cleanup skipped: {str(e)[:50]}...")
        # Don't let this error stop the bot from starting


def send_long_message(message: str, max_length: int = 4096):
    """
    Send long message by splitting it into chunks if needed
    Telegram has a 4096 character limit per message
    """
    if len(message) <= max_length:
        return send_telegram_message(message)
    
    # Split message into chunks
    messages = []
    current_message = ""
    
    for line in message.split('\n'):
        if len(current_message) + len(line) + 1 <= max_length:
            current_message += line + '\n'
        else:
            if current_message:
                messages.append(current_message.strip())
            current_message = line + '\n'
    
    if current_message:
        messages.append(current_message.strip())
    
    # Send each chunk
    responses = []
    for i, msg in enumerate(messages):
        if i > 0:
            # Add continuation marker for subsequent messages
            title_line = msg.split('\n')[0]
            if title_line.startswith('🔍'):
                # For research messages, add continuation marker
                msg = f"{title_line} (continued {i+1})\n" + '\n'.join(msg.split('\n')[1:])
        
        response = send_telegram_message(msg)
        responses.append(response)
    
    return responses