
class PromptTemplate:

    def run(self, prompt):
        return prompt


class Client:

    def generate(self, response_format="text"):
        return response_format


template = PromptTemplate()
client = Client()

# Rule R15: Rename run to invoke
result = template.run("Explain artificial intelligence")

# Rule R14: Replace response_format text with json
response = client.generate(response_format="text")

print(result)
print(response)
