"""Foreign-key update & delete policies.

Tables themselves are defined as Django models (`core/models.py`) and created
with `makemigrations` / `migrate`. This module owns ONLY the foreign-key
update/delete strategies, for two reasons:

  * The project bypasses the ORM for all queries (see `core/db.py`), so Django's
    `on_delete` — which the ORM enforces in Python, not in the database — never
    runs for our raw-SQL writes. The behaviour must be enforced at the DB level.
  * Django models cannot express `ON UPDATE` referential actions at all.

So after migrations create the tables and their default foreign keys, this
module replaces each foreign key with one that declares explicit ON UPDATE /
ON DELETE behaviour. Apply it (after every `migrate`) with:

    python manage.py apply_constraints

Statements are idempotent (drop-if-exists, then add) so they can be re-applied
safely. The identifiers below are trusted constants, not user input — building
DDL by formatting is fine here; the "no string-formatted SQL" rule is about
query parameters in `core/db.py`.
"""

# Each entry replaces one foreign key with an explicit update/delete policy.
# Add entries as the data model grows (the referenced tables must already exist,
# i.e. list them after the corresponding models have been migrated).
FK_POLICIES = [
    # Example — replace with the real zlagoda foreign keys:
    # {
    #     "table": "product",
    #     "constraint": "product_category_number_fk",
    #     "column": "category_number",
    #     "references": "category (category_number)",
    #     "on_update": "CASCADE",
    #     "on_delete": "NO ACTION",
    # },
]


def apply(cursor):
    """(Re)create each foreign key with its explicit update/delete policy."""
    for fk in FK_POLICIES:
        cursor.execute(
            f'ALTER TABLE {fk["table"]} '
            f'DROP CONSTRAINT IF EXISTS {fk["constraint"]}'
        )
        cursor.execute(
            f'ALTER TABLE {fk["table"]} '
            f'ADD CONSTRAINT {fk["constraint"]} '
            f'FOREIGN KEY ({fk["column"]}) REFERENCES {fk["references"]} '
            f'ON UPDATE {fk["on_update"]} ON DELETE {fk["on_delete"]}'
        )
