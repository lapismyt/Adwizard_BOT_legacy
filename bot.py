from telebot import TeleBot
from telebot import types
import g4f
import models

with open("token.txt") as f:
    token = f.read().strip()

bot = TeleBot(token)

@bot.message_handler(commands=["start"])
def cmd_start(message):
    data = models.Data.load()
    if data.get_user(message.from_user.id) is None:
        user = models.User(message.from_user.id)
        data.users.append(user)
        data.dump()
    bot.send_message(message.from_user.id, "Привет! Если не знаешь, с чего начать - спроси меня о чём-нибудь. Попроси расскзаать исторический факт, написать код, или сочинить стихотворение.")

@bot.message_handler(content_types=["text"])
def text_handler(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    user.settings.conversation.append({"role": "user", "content": message.text})
    response = g4f.ChatCompletion.create(
        model = user.settings.model,
        messages = user.settings.conversation
    )
    user.settings.conversation.append({"role": "assistant", "content": response})
    data.dump()
    bot.send_message(message.from_user.id, response, parse_mode="markdown")


if __name__ == "__main__":
    bot.infinity_polling()
