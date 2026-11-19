
class PromptTemplate:

    def run(self, prompt):
        return prompt


template = PromptTemplate()

result1 = template.invoke("Explain Python")
result2 = template.invoke("Explain Java")
result3 = template.invoke("Explain C++")

print(result1)
print(result2)
print(result3)
