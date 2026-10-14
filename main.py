from agent2.agent import CodeMigrationAgent


source_code = """
from old_library import OldClass


class MyClass:

    def hello(self):

        obj = OldClass()

        return obj


def create_object():

    return OldClass()
"""


agent = CodeMigrationAgent()

migration_maps = agent.generate_migration_map(
    source_code
)


print("\n" + "=" * 70)
print("MIGRATION MAP")
print("=" * 70)

for migration_map in migration_maps:

    print(migration_map)