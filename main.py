
# -*- coding: utf-8 -*-

import logging
import telegram, os
import requests
from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters

# Mistral API key
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") 

chat_language = os.getenv("INIT_LANGUAGE", default="zh")
MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default=20))
LANGUAGE_TABLE = {
    "zh": "哈囉！",
    "en": "Hello!",
    "jp": "こんにちは"
}

class Prompts:
    def __init__(self):
        self.msg_list = []
        self.msg_list.append(f"AI:{LANGUAGE_TABLE[chat_language]}")

    def add_msg(self, new_msg):
        if len(self.msg_list) >= MSG_LIST_LIMIT:
            self.remove_msg()
        self.msg_list.append(new_msg)

    def remove_msg(self):
        self.msg_list.pop(0)

    def generate_prompt(self):
        return "\n".join(self.msg_list)

class MistralChat:
    def __init__(self):
        self.prompt = Prompts()
        self.model = os.getenv("MISTRAL_MODEL", default="mistral-medium")

    def get_response(self):
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一個聰明的 AI 助理。"},
                {"role": "user", "content": self.prompt.generate_prompt()}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print("AI回答內容：")
            print(response.json()['choices'][0]['message']['content'].strip())
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print("AI原始回覆資料內容：")
            print(response.text)
            return f"[錯誤] Mistral API 回覆失敗：{response.status_code}"

    def add_msg(self, text):
        self.prompt.add_msg(text)

telegram_bot_token = str(os.getenv("TELEGRAM_BOT_TOKEN"))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initial Flask app
app = Flask(__name__)

# Initial bot by Telegram access token
bot = telegram.Bot(token=telegram_bot_token)

@app.route('/callback', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'ok'

def reply_handler(bot, update):
    chat = MistralChat()
    chat.prompt.add_msg(update.message.text)
    ai_reply = chat.get_response()
    update.message.reply_text(ai_reply)

dispatcher = Dispatcher(bot, None)
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

if __name__ == "__main__":
    app.run(debug=True)
