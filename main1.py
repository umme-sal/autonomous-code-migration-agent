from agent2.migration_engine import MigrationEngine


source_code = """
from old_library import OldClass


class MyClass:

    def hello(self):

        obj = OldClass()

        print("OldClass should stay here")

        return obj
"""


migration_map = {

    "old_library": {

        "module": "new_library",

        "names": {
            "OldClass": "NewClass"
        }
    }
}


engine = MigrationEngine()

migrated_code = engine.migrate(
    source_code,
    migration_map
)


print("=" * 60)
print("ORIGINAL")
print("=" * 60)

print(source_code)


print("=" * 60)
print("MIGRATED")
print("=" * 60)

print(migrated_code)