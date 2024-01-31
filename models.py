from msgspec import Struct
from msgspec.json import decode, encode

class UserSettings(Struct):
    conversation: list = [{"role": "system", "content": "You are a helpful assistant."}]
    scenario: str = "default"
    model: str = "gpt-3.5-turbo"

class User(Struct):
    id: str | int
    settings: UserSettings = UserSettings()

class Data(Struct):
    users: list[User]
    scenarios: dict = {"default": "You are a helpful assistant."}

    def get_scenario(self, scenario):
        if not scenario in self.scenarios.keys():
            return None
        else:
            return self.scenarios[scenario]

    def get_user(self, id):
        for usr in self.users:
            if usr.id == id:
                if usr.settings.model == "gpt-3.5-long":
                    usr.settings.model = "gpt-3.5-turbo-16k"
                if usr.settings.model == "gpt-3.5":
                    usr.settings.model == "gpt-3.5-turbo"
                return usr
        return None

    def dump(self):
         with open("data.json", "wb") as f:
            f.write(encode(self, indent=2))
    
    @staticmethod
    def load():
        with open("data.json", "rb") as f:
            data = decode(f.read(), type=Data, indent=2)
        return data
