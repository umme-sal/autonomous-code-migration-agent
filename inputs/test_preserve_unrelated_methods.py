
class Client:

    def run(self, prompt):
        return prompt

    def execute(self, command):
        return command

    def close(self):
        print("Client closed")


client = Client()

result = client.run("Hello")
execution = client.execute("print('Hello')")

client.close()

print(result)
