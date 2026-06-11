"""Django models — used ONLY to define tables and run migrations.

These models describe the database schema so that `makemigrations` / `migrate`
can create the tables. They are NOT used for queries: all reads and writes go
through raw SQL in `core/db.py`.

Foreign-key `on_delete` here only satisfies Django's field API — it is enforced
by the ORM in Python and does not apply to our raw-SQL writes. The real,
database-level update/delete policies are declared in `core/constraints.py` and
applied with `python manage.py apply_constraints` after migrating.

Example:

    class Category(models.Model):
        category_number = models.AutoField(primary_key=True)
        category_name = models.CharField(max_length=50, unique=True)

        class Meta:
            db_table = "category"
"""

from django.db import models  # noqa: F401
