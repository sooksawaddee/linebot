
import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from groq import Groq

app = Flask(__name__)

handler = WebhookHandler(
    os.environ["3a5de8696db014852d327a6b6e40ccad"]
)

config = Configuration(
    access_token=os.environ["R/JC9cpOtSuEkTqoXpWQ1qGCsvFo9OCLY0kivL/2tryUyFEUMB9SrhSWzoShYBa+BMfAgFU4QOMIpOFr8QP5J38XFI3EyaQ9HH/VhRQH/ljKpuUkWE1DtymuZI6RPnycb5tR1HpfMpuK/GxoCUIbOQdB04t89/1O/w1cDnyilFU="]
)

groq_client = Groq(
    api_key=os.environ["GROQ_API_KEY"]
)

@app.route("/", methods=["GET"])
def home():
    return "LINE Groq Bot is running!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    question = event.message.text

    try:
        result = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "ตอบคำถามเป็นภาษาไทยอย่างสุภาพและเข้าใจง่าย"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=500
        )
        answer = result.choices[0].message.content
    except Exception:
        app.logger.exception("Groq request failed")
        answer = "ขออภัย ระบบ AI ขัดข้องชั่วคราว"

    with ApiClient(config) as api_client:
        line_api = MessagingApi(api_client)
        line_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=answer[:5000])]
            )
        )
