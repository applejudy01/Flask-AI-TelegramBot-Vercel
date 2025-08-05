# -*- coding: utf-8 -*-

import logging
import os
import telegram

from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters

# 導入 Gemini API 函式庫
import google.generativeai as genai

# 設定 Gemini API 金鑰
# 請確保您已在環境變數中設定 GEMINI_API_KEY
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 聊天語言設定 (可選)
chat_language = os.getenv("INIT_LANGUAGE", default="zh")
MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default=20))
LANGUAGE_TABLE = {
    "zh": "哈囉！",
    "en": "Hello!",
    "jp": "こんにちは"
}

# ---
# 這是與 Gemini API 互動的核心類別
# ---
class GeminiBot:
    def __init__(self):
        # 初始化 Gemini 模型
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])

    def get_response(self, text):
        try:
            # 將使用者輸入的文字傳送給 Gemini 模型
            response = self.chat.send_message(text)

            # 取得 Gemini 的回覆內容
            ai_reply = response.text

            print("Gemini 回答內容：")
            print(ai_reply)

            return ai_reply
        except Exception as e:
            print(f"與 Gemini API 互動時發生錯誤：{e}")
            return "對不起，目前無法處理您的請求，請稍後再試。"

# ---
# Flask 應用程式設定
# ---
telegram_bot_token = str(os.getenv("TELEGRAM_BOT_TOKEN"))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telegram.Bot(token=telegram_bot_token)
gemini_bot_instance = GeminiBot() # 在全域範圍內建立一個 GeminiBot 實例

@app.route('/callback', methods=['POST'])
def webhook_handler():
    """設定路由 /callback，當有 POST 請求時會觸發此方法。"""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

def reply_handler(bot, update):
    """處理收到的訊息並回覆。"""
    user_text = update.message.text
    print(f"收到使用者訊息：{user_text}")

    # 傳送文字給 Gemini 模型並取得回覆
    ai_reply_response = gemini_bot_instance.get_response(user_text)

    # 用 AI 的文字回傳
    update.message.reply_text(ai_reply_response)

# 建立一個 bot dispatcher
dispatcher = Dispatcher(bot, None)

# 為文字訊息加入 handler
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

if __name__ == "__main__":
    # 執行伺服器
    app.run(debug=True)
