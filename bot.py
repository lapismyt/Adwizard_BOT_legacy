from telebot import TeleBot
from telebot import types
import openai
import models
import os
import time
import speech_recognition as sr
from pydub import AudioSegment

GPT_MODELS = [
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-16k-0613",
    "gpt-3.5-turbo-16k",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4-1106-preview"
]

openai.api_key = "sk-2AAszqIqRyl6KXxmC908BfB27fFb45C89714Ed8f0e22386a"
openai.api_base = "https://neuroapi.host/v1"

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
    bot.send_message(message.chat.id, "Привет! Если не знаешь, с чего начать - спроси меня о чём-нибудь. Ты можешь попросить меня рассказать исторический факт, написать код, или сочинить стихотворение.\n\nЧат - https://t.me/+cRAejyefoDsyMTky.")

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
        bot.send_message(message.chat.id, "Доступные модели:\n\n" + "\n".join(GPT_MODELS))
        return None
    m = message.text[7:]
    if m in GPT_MODELS:
        user.settings.model = m
        data.dump()
        bot.send_message(message.chat.id, f"Модель выбрана: {m}")
    else:
        bot.send_message(message.chat.id, "Неизвестная модель. Доступные модели:\n\n" + "\n".join(GPT_MODELS))

@bot.message_handler(commands=["scenario"])
def choose_scenario(message):
    if len(message.text) > 10:
        scenario = message.text.split()[1]
    else:
        bot.send_message(message.chat.id, "Использование: /scenario [сценарий]\n\nСценарии можно найти в нашем чате: https://t.me/+cRAejyefoDsyMTky.")
        return None
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    s = data.get_scenario(scenario)
    if s is None:
        bot.send_message(message.chat.id, "Сценарий не найден.")
    else:
        user.settings.scenario = scenario
        data.dump()
        bot.send_message(message.chat.id, f"Выбран сценарий: {scenario}. Используйте /clear для того, что бы он заработал.\n\nЧтобы вернуться к сценарию ао умолчанию, используйте /scenario default.\n\nЕсли сценарий не работает - попробуйте модель gpt-3.5-long.")

@bot.message_handler(commands=["make_scenario"])
def make_scenario(message):
    if len(message.text.split()) >= 3:
        data = models.Data.load()
        if message.text.split()[1] in data.scenarios.keys():
            bot.send_message(message.chat.id, "Сценарий уже существует.")
            return None
        cut = len(message.text.split()[1]) + 16
        data.scenarios[message.text.split()[1]] = message.text[cut:]
        data.dump()
        bot.send_message(message.chat.id, "Сценарий сохранён.")
    else:
        bot.send_message(message.chat.id, "Использование: /make_scenario [название] [промпт]")

@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    user.settings.conversation = user.settings.conversation[:-2]
    data.dump()
    bot.send_message(message.chat.id, "Отмена")

@bot.message_handler(content_types=["text"])
def text_handler(message):
    handle_req(message, message.text)

@bot.message_handler(content_types=["voice"])
def vc_handler(message):
    msg = bot.send_message(message.chat.id, "Распознаю голос...")
    voice_message = bot.get_file(message.voice.file_id)
    voice_file = bot.download_file(voice_message.file_path)
    vcid = f"vc-{int(time.time()*100)}"
    with open(f"tmp/{vcid}.ogg", "wb") as f:
        f.write(voice_file)
    audio = AudioSegment.from_ogg(f"tmp/{vcid}.ogg")
    audio.export(f"tmp/{vcid}.wav", format="wav")
    os.remove(f"tmp/{vcid}.ogg")
    recognizer = sr.Recognizer()
    with sr.AudioFile(f"tmp/{vcid}.wav") as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language='ru-RU')
    bot.send_message(message.chat.id, f"Распознано: {text}")
    bot.delete_message(msg.chat.id, msg.message_id)
    handle_req(message, text, vc=True)

def handle_req(message, text, vc=False):
    wait = bot.send_message(message.chat.id, "Думаю над ответом...")
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    try:
        conv = user.settings.conversation
        conv.append({"role": "user", "content": text})
        response = openai.ChatCompletion.create(
            model = user.settings.model,
            messages = conv,
            stream = False
        )
        response = response.choices[0].content
        user.settings.conversation = conv[:]
    except BaseException as err:
        bot.send_message(message.chat.id, "Ошибка!")
        print(repr(err))
        return None
    user.settings.conversation.append({"role": "assistant", "content": response})
    data.dump()
    bot.send_message(message.chat.id, response, parse_mode="markdown")
    bot.delete_message(wait.chat.id, wait.message_id)


if __name__ == "__main__":
    bot.infinity_polling()
