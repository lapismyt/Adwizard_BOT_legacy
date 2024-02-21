from telebot import TeleBot
from telebot import types
import models
from models import GPT_MODELS
import os
import time
import speech_recognition as sr
from pydub import AudioSegment
import openai
import random

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
    elif len(message.text) > 8:
        if message.text.removeprefix("/start ") in data.promos:
            user = data.get_user(message.from_user.id)
            user.premium = True
            data.promos.remove(message.text.removeprefix("/start "))
            data.dump()
            bot.send_message("5373440151", f"[{message.from_user.id}](tg://user?id={message.from_user.id}) активировал чек.", parse_mode="markdown")
            bot.send_message(message.chat.id, "Чек активирован.")
        else:
            bot.send_message(message.chat.id, "Чек уже активирован.")

@bot.message_handler(commands=["clear"])
def clear_context(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    s = data.get_scenario(user.settings.scenario)
    user.settings.conversation = [{"role": "system", "content": s}]
    data.dump()
    bot.send_message(message.chat.id, "*🧹 Переписка очищена.*", parse_mode="markdown")

@bot.message_handler(commands=["model"])
def switch_model(message):
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    if message.text.lower() == "/model":
        bot.send_message(message.chat.id, "*Доступные модели:\n\n" + "\n".join(GPT_MODELS) + "*\n\nТекущая модель: " + user.settings.model, parse_mode="markdown")
        return None
    m = message.text[7:]
    if not user.premium:
        bot.send_message(message.chat.id, "Смена моделей доступна только Premium-пользователям. Купить Premium навсегда за 250₽ -> @LapisMYT", parse_mode="markdown")
        return None
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

@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    data = models.Data.load()
    bot.send_message(message.chat.id, f"В боте на данный момент {len(data.users)} пользователей.")

@bot.message_handler(commands=["image"])
def cmd_image(message):
    if len(message.text) < 8:
        bot.send_message(message.chat.id, "Использование: /image [запрос]")
        return None
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    if user.queued:
        bot.send_message(message.chat.id, "*⏳ Подожди, пока выполнится предыдущий запрос.*", parse_mode="markdown")
        return None
    else:
        user.queued = True
        data.dump()
    msg = bot.send_message(message.chat.id, "Пожождите...")
    if user.premium:
        model = "dall-e-3"
        size = "1024x1024"
    else:
        model = "dall-e-2"
        size = "512x512"
    success = False
    for x in range(4):
        try:
            res = openai.Image.create(
                prompt = message.text.removeprefix("/image "),
                n = 1,
                size = size,
                model = model
            )
            bot.send_photo(message.chat.id, res["data"][0]["url"])
            bot.delete_message(msg.chat.id, msg.message_id)
            success = True
            break
        except BaseException as err:
            print(repr(err))
    if not success:
        bot.send_message(message.chat.id, "Ошибка!")
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    user.queued = False
    data.dump()

@bot.message_handler(commands=["premium"])
def cmd_premium(message):
    if not str(message.from_user.username) == "LapisMYT":
        return None
    if len(message.text) < 10:
        data = models.Data.load()
        cheque = str(random.randint(10000000, 99999999))
        data.promos.append(cheque)
        data.dump()
        bot.send_message(message.chat.id, f"https://t.me/Adwizard_BOT?start={cheque}")
    else:
        if len(message.text.split()) >= 2:
            data = models.Data.load()
            user = data.get_user(message.text.split()[1])
            if not len(message.text.split()) == 3:
                bot.send_message(message.chat.id, f"У пользователя [{message.text.split()[1]}](tg://user?id={message.text.split()[1]}) есть Premium: {user.premium}", parse_mode="markdown")
                return None
            elif message.text.split()[2] == "on":
                user.premium = True
                data.dump()
                try:
                    bot.send_message(message.text.split()[1], "У вас больше нет Premium!")
                except:
                    pass
                bot.send_message(message.chat.id, f"У пользователя [{message.text.split()[1]}](tg://user?id={message.text.split()[1]}) больше нет Premium.", parse_mode="markdown")
                return None
            elif message.text.split()[2] == "off":
                user.premium = False
                data.dump()
                try:
                    bot.send_message(message.text.split()[1], "У вас больше нет Premium!")
                except:
                    pass
                bot.send_message(message.chat.id, f"У пользователя [{message.text.split()[1]}](tg://user?id={message.text.split()[1]}) теперь есть Premium.", parse_mode="markdown")
                return None

@bot.message_handler(content_types=["text"])
def text_handler(message):
    text = message.text
    if message.chat.type == "private":
        pass
    elif message.text.strip().lower().startswith("@adwizard_bot"):
        text = message.text.removeprefix("@Adwizard_BOT").strip()
    elif hasattr(message, "reply_to_message"):
        if message.reply_to_message is None:
            return None
        if not str(message.reply_to_message.from_user.id) == "6342888297":
            return None
        handle_req(message, text)
        return None
    elif message.text.startswith("/"):
        return None
    else:
        return None
    handle_req(message, text)

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
    bot.reply_to(message, f"*❗ Расшифровано: {text}*", parse_mode="markdown")
    bot.delete_message(msg.chat.id, msg.message_id)
    if (not "chatgpt" in text.lower()) and (not message.chat.type == "private"):
        return None
    elif hasattr(message, "reply_to_message"):
        if message.reply_to_message is None:
            return None
        if not str(message.reply_to_message.from_user.id) == "6342888297":
            return None
    handle_req(message, text)

def handle_req(message, text, skipped=False):
    wait = bot.send_message(message.chat.id, "*👨‍💻 Печатаю...*", parse_mode="markdown")
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    if user.queued:
        m = bot.send_message(message.chat.id, "*⏳ Подожди, пока выполнится предыдущий запрос.*", parse_mode="markdown")
        if not chat.type == "private":
            time.sleep(3)
            bot.delete_message(m.chat.id, m.message_id)
        return None
    else:
        user.queued = True
        data.dump()
    success = False
    tries = 0
    while (not success) and (tries <= 5):
        try:
            conv = user.settings.conversation
            if not skipped:
                conv.append({"role": "user", "content": text})
            else:
                conv.append({"role": "system", "content": "Continue, please"})
            response = openai.ChatCompletion.create(
                model = user.settings.model,
                messages = conv,
                temperature = 0.8,
                stream = False,
                max_tokens = 2048
            )
            response = response.choices[0].message.content
            data = models.Data.load()
            user = data.get_user(message.from_user.id)
            user.settings.conversation = conv[:]
            user.settings.conversation.append({"role": "assistant", "content": response})
            user.queued = False
            data.dump()
            bot.reply_to(message, response, parse_mode="markdown")
            bot.delete_message(wait.chat.id, wait.message_id)
            success = True
            return None
        except openai.error.InvalidRequestError as err:
            print(repr(err))
            tries = 6
            bot.reply_to(message, "Слишком длинный контекст. Используйте /clear.")
        except BaseException as err:
            print(repr(err))
            time.sleep(3)
            tries += 1
    bot.reply_to(message, "*⛔ Ошибка!*", parse_mode="markdown")
    data = models.Data.load()
    user = data.get_user(message.from_user.id)
    user.queued = False
    data.dump()

if __name__ == "__main__":
    data = models.Data.load()
    for usr in data.users:
        usr.queued = False
    data.dump()
    bot.infinity_polling()
