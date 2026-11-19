
class Client:

    def run(self, prompt):
        return prompt


def process_request(client, prompt):

    result = client.invoke(prompt)

    return result


client = Client()

answer = process_request(
    client,
    "Explain machine learning"
)

print(answer)
