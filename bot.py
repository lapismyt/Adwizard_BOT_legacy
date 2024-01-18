from telebot import TeleBot
from telebot import types
import g4f
import models
import os
import time

GPT_MODELS = [
    "gpt-3.5-turbo"
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613"
    "gpt-4-0613",
    "code-davinci-002",
    "text-davinci-003",
    "text-ada-001",
    "text-curie-001",
    "text-babbage-001"
]

with open("token.txt") as f:
    token = f.read().strip()

bot = TeleBot(token)

@bot.message_handler(commands=["copy"])
def copy(message):
    os.system(f"cp data.json copies/data-{int(time.time())}.json")
    with open("data.json", "rb") as f:
        bot.send_document(message.from_user.id, f)
    bot.send_message(message.chat.id, "Резервная копия создана.")

@bot.message_handler(commands=["start"])
def cmd_start(message):
    data = models.Data.load()
    if data.get_user(message.from_user.id) is None:
        user = models.User(message.from_user.id)
        data.users.append(user)
        data.dump()
    bot.send_message(message.chat.id, "Привет! Если не знаешь, с чего начать - спроси меня о чём-нибудь. Ты можешь попросить меня рассказать исторический факт, написать код, или сочинить стихотворение.")

@bot.message_handler(commands=["clear"])
def clear_context(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    s = data.get_scenario(user.settings.scenario)
    user.settings.conversation = [{"role": "system", "content": s}]
    data.dump()
    bot.send_message(message.from_user.id, "Переписка очищена.")

@bot.message_handler(commands=["model"])
def switch_model(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    if message.text.lower() == "/model":
        bot.send_message(message.chat.id, "Доступные модели:\n\n" + "\n\n".join(GPT_MODELS))
        return None
    m = message.text[7:]
    if m in GPT_MODELS:
        user.settings.model = m
        data.dump()
        bot.send_message(message.chat.id, f"Модель выбрана: {m}")
    else:
        bot.send_message(message.chat.id, "Неизвестная модель. Доступные модели:\n\n" + "\n\n".join(GPT_MODELS))

@bot.message_handler(commands=["scenario"])
def choose_scenario(message):
    if len(message.text) > 10:
        scenario = message.text.split()[1]
    else:
        bot.send_message(message.chat.id, "Использование: /scenario [сценарий]")
        return None
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    s = data.get_scenario(scenario)
    if s is None:
        bot.send_message(message.chat.id, "Сценарий не найден.")
    else:
        user.settings.scenario = scenario
        data.dump()
        bot.send_message(message.chat.id, f"Выбран сценарий: {scenario}. Используйте /clear для того, что бы он заработал.")

@bot.message_handler(commands=["make_scenario"])
def make_scenario(message):
    if len(message.text.split()) >= 3:
        data = models.Data.load()
        if message.text.split()[1] in data.scenarios.keys():
            return None
        cut = len(message.text.split()[1]) + 16
        data.scenarios[message.text.split()[1]] = message.text[cut:]
        data.dump()
        bot.send_message(message.chat.id, "Сценарий сохранён.")
    else:
        bot.send_message(message.chat.id, "Использование: /make_scenario [название] [промпт]")

@bot.message_handler(content_types=["text"])
def text_handler(message):
    wait = bot.send_message(message.chat.id, "Пожалуйста, подождите...")
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    user.settings.conversation.append({"role": "user", "content": message.text})
    response = g4f.ChatCompletion.create(
        model = user.settings.model,
        messages = user.settings.conversation
    )
    user.settings.conversation.append({"role": "assistant", "content": response})
    data.dump()
    bot.send_message(message.chat.id, response, parse_mode="markdown")
    bot.delete_message(wait.chat.id, wait.message_id)


if __name__ == "__main__":
    bot.infinity_polling()
