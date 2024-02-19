from telebot import TeleBot
from telebot import types
#import g4f
import models
import os
import time
import speech_recognition as sr
from pydub import AudioSegment
import openai
#from g4f.Provider import FreeGpt, You, Chatgpt4Online, ChatgptDemoAi, ChatgptNext, ChatgptDemo, Gpt6, RetryProvider, GeekGpt, Liaobots, Theb, Raycast, FreeChatgpt, OpenaiChat, Bing, GptChatly, Aichat, GptGo, GeminiProChat, Koala, Aura, FakeGpt, AiAsk

GPT_MODELS = [
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-instruct",
    "gpt-3.5-turbo-instruct-0914",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4-1106-preview",
    "gpt-4-turbo-preview",
    "gpt-4-0125-preview",
]

openai.api_base = "https://api.proxyapi.ru/openai/v1"

with open("token.txt") as f:
    token = f.read().strip()

bot = TeleBot(token)

@bot.message_handler(commands=["copy"])
def copy(message):
    filename = f"data-{int(time.time())}.json"
    os.system(f"cp data.json copies/{filename}")
    with open(f"copies/{filename}", "rb") as f:
        bot.send_document(message.from_user.id, f)
    bot.send_message(message.chat.id, "Резервная копия создана.")

@bot.message_handler(commands=["start"])
def cmd_start(message):
    data = models.Data.load()
    if data.get_user(message.from_user.id) is None:
        user = models.User(message.from_user.id)
        data.users.append(user)
        data.dump()
    bot.send_message(message.chat.id, "*Привет! Если не знаешь, с чего начать - спроси меня о чём-нибудь. Модешь отправить свой вопрос текстом или голосовым сообщением. Ты можешь попросить меня рассказать исторический факт, написать код, или сочинить стихотворение.\n\nЧат - https://t.me/+cRAejyefoDsyMTky.*", disable_web_page_preview=True, parse_mode="markdown")
    bot.send_message(message.chat.id, "*Я поддерживаю сценарии - системные инструкции для определения моего поведения. Текстовая игра, виртуальная девушка, специалист в определённой сфере, имитация Linux-терминала - почти всё, что может быть связано с текстом, могу делать я, главное выбрать нужный сценарий. Найти сценарии можно в нашем чате - https://t.me/+cRAejyefoDsyMTky.*", disable_web_page_preview=True, parse_mode="markdown")

@bot.message_handler(commands=["clear"])
def clear_context(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    s = data.get_scenario(user.settings.scenario)
    user.settings.conversation = [{"role": "system", "content": s}]
    data.dump()
    bot.send_message(message.from_user.id, "*🧹 Переписка очищена.*", parse_mode="markdown")

@bot.message_handler(commands=["model"])
def switch_model(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    if message.text.lower() == "/model":
        bot.send_message(message.chat.id, "*Доступные модели:\n\n" + "\n".join(GPT_MODELS) + "*\n\nТекущая модель: " + user.settings.model, parse_mode="markdown")
        return None
    m = message.text[7:]
    if m in GPT_MODELS:
        user.settings.model = m
        data.dump()
        bot.send_message(message.chat.id, f"*Модель выбрана: {m}.*", parse_mode="markdown")
    else:
        bot.send_message(message.chat.id, "*Неизвестная модель. Доступные модели:\n\n" + "\n".join(GPT_MODELS) + "*", parse_mode="markdown")

@bot.message_handler(commands=["scenario"])
def choose_scenario(message):
    if len(message.text) > 10:
        scenario = message.text.split()[1]
    else:
        bot.send_message(message.chat.id, "*Использование: `/scenario [сценарий]`\n\nСценарии можно найти в нашем чате: https://t.me/+cRAejyefoDsyMTky.*", parse_mode="markdown", disable_web_page_preview=True)
        return None
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    s = data.get_scenario(scenario)
    if s is None:
        bot.send_message(message.chat.id, "Сценарий не найден.")
    else:
        user.settings.scenario = scenario
        data.dump()
        bot.send_message(message.chat.id, f"*Выбран сценарий: {scenario}. Используйте `/clear` для того, что бы он заработал.\n\nЧтобы вернуться к сценарию ао умолчанию, используйте `/scenario default.`\n\nЕсли сценарий не работает - попробуйте выбрать другую модель.*", parse_mode="markdown")

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
        bot.send_message(message.chat.id, "*🗒 Сценарий сохранён.*", parse_mode="markdown")
    else:
        bot.send_message(message.chat.id, "*Использование: /make_scenario [название] [промпт]*")

@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    user.settings.conversation = user.settings.conversation[:-2]
    data.dump()
    a = bot.send_message(message.chat.id, "*🕓 Отматываю время назад...*", parse_mode="markdown")
    time.sleep(1)
    bot.send_message(message.chat.id, "*✨ Ваш предыдущий запрос стёрт из этой временной линии!*", parse_mode="markdown")
    bot.delete_message(a.chat.id, a.message_id)

@bot.message_handler(commands=["sendall"])
def cmd_sendall(message):
    if message.from_user.id == 5373440151:
        data = models.Data.load()
        for usr in data.users:
            try:
                bot.forward_message(message.chat.id, usr.id, message.reply_to_message.message_id)
            except:
                print("Ашыпка!")

@bot.message_handler(content_types=["text"])
def text_handler(message):
    handle_req(message, message.text)

@bot.message_handler(commands=["skip"])
def cmd_skip(message):
    handle_req(message, None, skipped=True)

@bot.message_handler(content_types=["voice"])
def vc_handler(message):
    msg = bot.send_message(message.chat.id, "*🔊 Слушаю...*", parse_mode="markdown")
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
    bot.send_message(message.chat.id, f"*❗ Отвечаю на запрос: {text}*", parse_mode="markdown")
    bot.delete_message(msg.chat.id, msg.message_id)
    handle_req(message, text)

def handle_req(message, text, skipped=False):
    wait = bot.send_message(message.chat.id, "*👨‍💻 Печатаю...*", parse_mode="markdown")
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    success = False
    tries = 0
    while (not success) and (tries <= 5):
        try:
            conv = user.settings.conversation
            if not skipped:
                conv.append({"role": "user", "content": text})
            else:
                conv.append({"role": "system", "content": "continue"})
            #if "gpt-3.5-turbo" in user.settings.model:
            #    provider = RetryProvider([FreeGpt, Chatgpt4Online, ChatgptDemoAi, ChatgptNext, ChatgptDemo, Gpt6, GeekGpt, Liaobots, FreeChatgpt, GptChatly, Aichat, GptGo, FakeGpt, AiAsk])
            #elif "gpt-4" in user.settings.model:
            #    provider = RetryProvider([Bing, GeekGpt, Liaobots, Theb, Raycast, FreeChatgpt])
            #else:
            #    provider = None
            response = openai.ChatCompletion.create(
                model = user.settings.model,
                messages = conv,
                temperature = 0.7,
                stream = False
            )
            response = response.choices[0].message.content
            user.settings.conversation = conv[:]
            user.settings.conversation.append({"role": "assistant", "content": response})
            data.dump()
            bot.send_message(message.chat.id, response, parse_mode="markdown")
            bot.delete_message(wait.chat.id, wait.message_id)
            success = True
            return None
        except BaseException as err:
            print(repr(err))
            time.sleep(3)
            tries += 1
    bot.send_message(message.chat.id, "*⛔ Ошибка!*", parse_mode="markdown")


if __name__ == "__main__":
    bot.infinity_polling()
