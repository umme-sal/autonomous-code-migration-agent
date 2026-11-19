
class APIClient:

    def request(self, endpoint, payload):
        print("Sending request:", endpoint)
        return {"status": "success", "data": payload}

    def generate(self, prompt):
        print("Generating response:", prompt)
        return "Generated response"


class FileManager:

    def open_file(self, filename, legacy_mode=False):
        print("Opening:", filename)
        return filename


class Application:

    def __init__(self):
        self.client = APIClient()
        self.file_manager = FileManager()

    def process_request(self, endpoint, payload):

        response = self.client.request(
            endpoint,
            payload
        )

        return response

    def generate_report(self, prompt):

        result = self.client.generate(prompt)

        return result

    def load_configuration(self, filename):

        config = self.file_manager.open_file(
            filename,
            legacy_mode=True
        )

        return config


def main():

    app = Application()

    # API request
    response = app.process_request(
        "/users",
        {"name": "Anya"}
    )

    # Generate content
    report = app.generate_report(
        "Explain distributed systems"
    )

    # Open configuration
    config = app.load_configuration(
        "settings.json"
    )

    print(response)
    print(report)
    print(config)


if __name__ == "__main__":
    main()
