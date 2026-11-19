
class Client:

    def run(self, data):
        return data


client1 = Client()
client2 = Client()

first_result = client1.invoke("Python")
second_result = client2.invoke("Java")

print(first_result)
print(second_result)
