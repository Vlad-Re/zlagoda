from django.test import TestCase, Client
from django.core.management import call_command
from core import queries


class BaseZlagodaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Apply DB policies and create basic reference data once for all tests."""
        call_command("apply_constraints")

        # Create basic category and product
        queries.execute(
            "INSERT INTO category (category_number, category_name) VALUES (%s, %s)",
            [1, "Тестова категорія"],
        )
        queries.execute(
            "INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES (%s, %s, %s, %s)",
            [100, 1, "Тестовий товар", "Характеристики"],
        )

        # Create employee
        queries.execute(
            """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            [
                "EMP_TEST",
                "Тестер",
                "Іван",
                "Cashier",
                15000,
                "1990-01-01",
                "2023-01-01",
                "+380990000000",
                "Київ",
                "Вулиця",
                "00000",
                '',
            ],
        )

    def setUp(self):
        """Initialize client before each individual test and log in as Manager."""
        self.client = Client()

        # Глобальна авторизація для ВСІХ тестів
        session = self.client.session
        session["employee_id"] = "EMP_TEST"
        session["role"] = "Manager"  # Менеджер має доступ до всього
        session.save()
