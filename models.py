from msgspec import Struct
from msgspec.json import decode, encode

class UserSettings(Struct):
    conversation: list = []
    scenario: str = "default"
    model: str = "gpt-4-0613"

class User(Struct):
    id: str | int
    settings: UserSettings = UserSettings()

class Data(Struct):
    users: list[User]
    scenarios: dict = {"default": "You are a helpful assistant".}

    def get_scenario(self, scenario):
        if not scenario in self.scenarios.keys():
            return None
        else:
            return self.scenarios[scenario]

    def get_user(self, id):
        for usr in self.users:
            if usr.id == id:
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
