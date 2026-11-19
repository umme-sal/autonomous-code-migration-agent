
from legacy_sdk.models import ChatModel
from legacy_sdk.storage import VectorDB
from legacy_sdk import old_connect, LegacyError


def old_client(model_name="legacy-model"):
    return ChatModel(model_name=model_name)


def load_model(model_name="legacy-model"):
    return ChatModel(model_name=model_name)


def create_model(model_name="legacy-model", temperature=0.7):
    return ChatModel(
        model_name=model_name,
        temperature=temperature
    )


class LegacyBase:
    pass


class Worker(LegacyBase):
    def execute(self, prompt):
        return prompt


class Application:

    def __init__(self, api_key, endpoint):
        self.client = old_connect(
            api_key=api_key,
            endpoint=endpoint
        )

    def generate(self, prompt):
        return self.client.generate(
            prompt,
            response_format="text"
        )

    def predict(self, prompt):
        return self.client.predict(
            prompt,
            temperature=0.7
        )

    def process(self, prompt):
        result = self.client.run(prompt)
        return result

    def load_document(self, filename):
        return self.client.open_file(
            filename,
            legacy_mode=True
        )

    def request_data(self, endpoint, payload):
        return self.client.request(
            endpoint,
            payload
        )

    def handle_request(self, prompt):
        try:
            return self.generate(prompt)
        except LegacyError:
            print("Something went wrong")


def main():
    app = Application(
        api_key="demo-key",
        endpoint="https://old-api.example.com"
    )

    response = app.generate("Explain AI agents")
    print(response)


if __name__ == "__main__":
    main()
