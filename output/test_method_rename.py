
class PromptTemplate:

    def run(self, prompt):
        return prompt


template = PromptTemplate()

result = template.invoke("Explain Python decorators")

print(result)
