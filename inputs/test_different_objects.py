
class Client:

    def run(self, data):
        return data


client1 = Client()
client2 = Client()

first_result = client1.run("Python")
second_result = client2.run("Java")

print(first_result)
print(second_result)
