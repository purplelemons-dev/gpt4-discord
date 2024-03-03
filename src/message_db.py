from openai.types.chat import ChatCompletionMessageParam


class MessageDatabase:
    def __init__(self, db: dict[int, list[ChatCompletionMessageParam]] = None):
        if db is not None:
            self.db = db
        else:
            self.db: dict[int, list[ChatCompletionMessageParam]] = {}

    def get_messages(self, user_id: int):
        try:
            out = self.db[user_id]
        except KeyError:
            out = []
            self.db[user_id] = out
        return out

    def add_message(self, user_id, message):
        try:
            self.db[user_id].append(message)
        except KeyError:
            self.db[user_id] = [message]

    def __getitem__(self, user_id: int):
        return self.get_messages(user_id)

    def __setitem__(self, user_id: int, message: ChatCompletionMessageParam):
        self.add_message(user_id, message)
