class UserMessage:
    def __init__(self, text):
        self.text = text

class LlmChat:
    def __init__(self, *args, **kwargs):
        pass

    def with_model(self, *args, **kwargs):
        return self

    async def send_message(self, message):
        return "Mock response"
