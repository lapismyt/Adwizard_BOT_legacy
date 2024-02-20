from msgspec import Struct
from msgspec.json import decode, encode

GPT_MODELS = [
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613",
    "gpt-3.5-turbo-instruct",
    "gpt-3.5-turbo-instruct-0914",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4-1106-preview",
    "gpt-4-turbo-preview",
    "gpt-4-0125-preview",
]

class UserSettings(Struct):
    conversation: list = [{"role": "system", "content": "You are a helpful assistant."}]
    scenario: str = "default"
    model: str = "gpt-3.5-turbo"

class User(Struct):
    id: str | int
    settings: UserSettings = UserSettings()
    queued: bool = False
    premium: bool = False

class Data(Struct):
    users: list[User]
    promos: list = [] 
    scenarios: dict = {"default": "You are a helpful assistant."}

    def get_scenario(self, scenario):
        if not scenario in self.scenarios.keys():
            return None
        else:
            return self.scenarios[scenario]

    def get_user(self, id):
        for usr in self.users:
            if str(usr.id) == str(id):
                if not usr.settings.model in GPT_MODELS:
                    usr.settings.model = "gpt-3.5-turbo"
                if usr.premium == False:
                    usr.settings.model = "gpt-3.5-turbo"
                return usr
        return None

    def dump(self):
         with open("data.json", "wb") as f:
            f.write(encode(self))
    
    @staticmethod
    def load():
        with open("data.json", "rb") as f:
            data = decode(f.read(), type=Data)
        return data
