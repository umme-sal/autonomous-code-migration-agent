
class PromptTemplate:

    def run(self, prompt):
        return prompt


template = PromptTemplate()

result = template.run("Explain Python decorators")

print(result)
