
class Client:

    def run(self, prompt):
        return prompt


def process_request(client, prompt):

    result = client.run(prompt)

    return result


client = Client()

answer = process_request(
    client,
    "Explain machine learning"
)

print(answer)
