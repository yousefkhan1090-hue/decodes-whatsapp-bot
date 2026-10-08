import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# ==================== CONFIGURATION ====================
# 1. Google Gemini Setup (Free from https://aistudio.google.com)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=GEMINI_API_KEY)

# 2. Meta WhatsApp Cloud API Setup (From Facebook Developer Console)
WHATSAPP_TOKEN = "YOUR_META_ACCESS_TOKEN"
PHONE_NUMBER_ID = "YOUR_META_PHONE_NUMBER_ID"
VERIFY_TOKEN = "my_custom_secure_token_123"  # Set any word here to verify webhook

# ==================== BUSINESS KNOWLEDGE BASE ====================
SYSTEM_INSTRUCTION = """
You are the official AI representative for DeCodeS Tech, a digital agency in Pakistan.
Speak politely, warmly, and like a human team member. Keep answers concise for WhatsApp.

Services Offered:
- Website Development (Fast, responsive, SEO-friendly)
- UX/UI Design
- Graphic Design & Branding
- Digital Marketing, Social Media Marketing & Google Ads
- Generative AI & Promotional Videos

Contact Information:
- Address: Al Qadir Plaza, Ground floor, Garden Town, Dera Ghazi Khan, Pakistan
- Phone: 0330-3682001
- Email: contact@decodtech.com
- Working Hours: Monday - Saturday | 9:00 AM - 5:00 PM

Goal: Answer customer questions accurately and encourage them to book a free consultation!
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# ==================== HELPER FUNCTIONS ====================
def send_whatsapp_message(recipient_id, text_body):
    """Sends a text message back to the user via WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": text_body}
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# ==================== WEBHOOK ROUTES ====================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Webhook verification step for Meta."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    """Processes incoming WhatsApp messages."""
    data = request.json

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]
            
            # Check if message is plain text
            if message["type"] == "text":
                user_text = message["text"]["body"]
                print(f"Received message: {user_text} from {from_number}")

                # Generate answer using Gemini AI
                ai_response = model.generate_content(user_text)
                reply_text = ai_response.text

                # Send reply to WhatsApp
                send_whatsapp_message(from_number, reply_text)

    except Exception as e:
        print(f"Error handling message: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    # Runs the local Webhook listener
    app.run(host="0.0.0.0", port=5000)