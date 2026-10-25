import os
import logging

from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

from groq import Groq


# ==========================================
# 1. Flask Application
# ==========================================

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================
# 2. Environment Variables
# ==========================================

LINE_CHANNEL_SECRET = os.getenv("3a5de8696db014852d327a6b6e40ccad")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("R/JC9cpOtSuEkTqoXpWQ1qGCsvFo9OCLY0kivL/2tryUyFEUMB9SrhSWzoShYBa+BMfAgFU4QOMIpOFr8QP5J38XFI3EyaQ9HH/VhRQH/ljKpuUkWE1DtymuZI6RPnycb5tR1HpfMpuK/GxoCUIbOQdB04t89/1O/w1cDnyilFU=")
GROQ_API_KEY = os.getenv("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")

required_vars = {
    "LINE_CHANNEL_SECRET": LINE_CHANNEL_SECRET,
    "LINE_CHANNEL_ACCESS_TOKEN": LINE_CHANNEL_ACCESS_TOKEN,
    "GROQ_API_KEY": GROQ_API_KEY
}

for name, value in required_vars.items():
    if not value:
        raise RuntimeError(
            f"Missing environment variable: {name}"
        )


# ==========================================
# 3. LINE Messaging API Configuration
# ==========================================

handler = WebhookHandler(
    LINE_CHANNEL_SECRET
)

line_config = Configuration(
    access_token=LINE_CHANNEL_ACCESS_TOKEN
)


# ==========================================
# 4. Groq AI Configuration
# ==========================================

groq_client = Groq(
    api_key=GROQ_API_KEY,
    timeout=15.0,
    max_retries=0
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


# ==========================================
# 5. Home Route
# ==========================================

@app.route("/", methods=["GET"])
def home():
    return {
        "status": "online",
        "service": "LINE OA + Groq AI Bot",
        "message": "LINE Groq Bot is running!"
    }, 200


# ==========================================
# 6. LINE Webhook
# ==========================================

@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers.get(
        "X-Line-Signature", ""
    )

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        logger.warning("Invalid LINE signature")
        abort(400)

    except Exception:
        logger.exception("Webhook processing failed")
        abort(500)

    return "OK", 200


# ==========================================
# 7. Groq AI Function
# ==========================================

def ask_groq(question):

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "คุณเป็นผู้ช่วย AI ของ LINE Official Account "
                        "ตอบคำถามเป็นภาษาไทยอย่างสุภาพ "
                        "ให้ข้อมูลถูกต้อง กระชับ และเข้าใจง่าย "
                        "หากไม่ทราบคำตอบ ให้บอกตามตรง "
                        "ห้ามสร้างข้อมูลที่ไม่มีแหล่งอ้างอิง"
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ],

            temperature=0.5,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if not answer:
            return "ขออภัย AI ไม่สามารถสร้างคำตอบได้"

        return answer.strip()

    except Exception:
        logger.exception("Groq API Error")

        return (
            "ขออภัยครับ ระบบ AI ขัดข้องชั่วคราว "
            "กรุณาลองใหม่อีกครั้ง"
        )


# ==========================================
# 8. LINE Message Handler
# ==========================================

@handler.add(
    MessageEvent,
    message=TextMessageContent
)
def handle_message(event):

    user_message = event.message.text.strip()

    logger.info("Received LINE text message")

    if not user_message:
        answer = "กรุณาพิมพ์คำถามที่ต้องการสอบถามครับ"

    else:
        answer = ask_groq(user_message)

    # LINE Text Message Limit
    answer = answer[:5000]

    try:
        with ApiClient(line_config) as api_client:

            line_api = MessagingApi(api_client)

            line_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,

                    messages=[
                        TextMessage(
                            text=answer
                        )
                    ]
                )
            )

        logger.info("LINE reply sent successfully")

    except Exception:
        logger.exception("LINE Reply API Error")
        raise


# ==========================================
# 9. Run Application
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
