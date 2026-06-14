"""Apply the foreign-key update/delete policies from core/constraints.py.

Run this AFTER `migrate` (which creates the tables and their default foreign
keys). It replaces those foreign keys with ones that have explicit DB-level
ON UPDATE / ON DELETE behaviour, since the ORM is bypassed for all queries.

    python manage.py apply_constraints
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from core import constraints


class Command(BaseCommand):
    help = "Apply foreign-key update/delete policies from core/constraints.py"

    def handle(self, *args, **options):
        with transaction.atomic(), connection.cursor() as cursor:
            constraints.apply(cursor)
        self.stdout.write(
            self.style.SUCCESS(
                f"Applied {len(constraints.SQL_CONSTRAINTS)} SQL constraints."
            )
        )
