
class PromptTemplate:

    def run(self, prompt):
        return prompt


template = PromptTemplate()

result1 = template.run("Explain Python")
result2 = template.run("Explain Java")
result3 = template.run("Explain C++")

print(result1)
print(result2)
print(result3)
