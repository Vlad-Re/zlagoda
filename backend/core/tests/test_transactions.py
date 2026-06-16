import json
import threading
from django.test import TransactionTestCase, Client
from django.core.management import call_command
from django.db import connection

from core import queries
from .test_base import BaseZlagodaTest


class CheckTransactionTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute("DELETE FROM store_product")
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
               VALUES ('123456789012', 100, 40.00, 10, FALSE)"""
        )

    def test_successful_check_creation(self):
        """Test successful check creation (product deduction and correct sum calculation)."""
        payload = {
            "check_number": "CHK001",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "123456789012", "product_number": 3}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CHK001'"
        )
        self.assertIsNotNone(check)
        self.assertEqual(float(check["sum_total"]), 120.00)

        product_in_store = queries.fetch_one(
            "SELECT products_number FROM store_product WHERE \"UPC\" = '123456789012'"
        )
        self.assertEqual(product_in_store["products_number"], 7)

    def test_failed_transaction_rollback_due_to_amount(self):
        """Test ACID: attempt to sell more than available in store."""
        payload = {
            "check_number": "CHK002",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "123456789012", "product_number": 15}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CHK002'"
        )
        self.assertIsNone(check)

        product_in_store = queries.fetch_one(
            "SELECT products_number FROM store_product WHERE \"UPC\" = '123456789012'"
        )
        self.assertEqual(product_in_store["products_number"], 10)

    # ... попередні методи класу CheckTransactionTests ...

    def test_checkout_out_of_stock_fails(self):
        """Case 11: Attempt to buy an item with 0 stock should fail via DB constraint."""
        # Manually set stock to 0
        queries.execute(
            "UPDATE store_product SET products_number = 0 WHERE \"UPC\" = '123456789012'"
        )

        payload = {
            "check_number": "CH_OOS",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "123456789012", "product_number": 1}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )

        # Expect 400 because attempting to sell more than available stock raises IntegrityError,
        # which is caught by the API view and returned as a 400 Bad Request.
        self.assertEqual(response.status_code, 400)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CH_OOS'"
        )
        self.assertIsNone(check)

    def test_checkout_without_customer_card_success(self):
        """Case 14: Checkout successfully processes when card_number is None."""
        payload = {
            "check_number": "CH_NOCARD",
            "id_employee": "EMP_TEST",
            "card_number": None,
            "products": [{"UPC": "123456789012", "product_number": 2}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CH_NOCARD'"
        )
        self.assertIsNotNone(check)
        self.assertIsNone(check["card_number"])

    def test_create_check_with_empty_products_fails(self):
        """Case 17: Ghost check prevention. Payload with empty products array should be rejected before hitting DB."""
        payload = {
            "check_number": "CH_GHOST",
            "id_employee": "EMP_TEST",
            "products": [],
        }
        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CH_GHOST'"
        )
        self.assertIsNone(check)

    def test_regular_and_promo_in_same_check(self):
        """Case 18: Buying a regular item and its promotional counterpart in the same check is valid."""
        queries.execute(
            """INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product)
                           VALUES ('PROM_123', '123456789012', 100, 30.00, 10, TRUE)"""
        )

        payload = {
            "check_number": "CH_MIX",
            "id_employee": "EMP_TEST",
            "products": [
                {"UPC": "123456789012", "product_number": 1},
                {"UPC": "PROM_123", "product_number": 1},
            ],
        }
        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        items = queries.fetch_all("SELECT * FROM sale WHERE check_number = 'CH_MIX'")
        self.assertEqual(len(items), 2)

        # ... попередні методи класу CheckTransactionTests ...

    def test_duplicate_upc_in_checkout_fails(self):
        """Case 21: Payload with duplicate UPCs should fail due to unique_together ('UPC', 'check_number') in DB."""
        payload = {
            "check_number": "CH_DUP",
            "id_employee": "EMP_TEST",
            "products": [
                {"UPC": "123456789012", "product_number": 1},
                {"UPC": "123456789012", "product_number": 2},  # Дублікат!
            ],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )

        # Expect 400 because IntegrityError is raised on the second insert into 'sale'
        self.assertEqual(response.status_code, 400)

        # ACID check: check should not be created
        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CH_DUP'"
        )
        self.assertIsNone(check)

    def test_rounding_discrepancy(self):
        """Case 23: Test that float operations and Decimal(13,4) DB mapping don't lose fractions."""
        # Set a tricky price with 4 decimal places
        queries.execute(
            "UPDATE store_product SET selling_price = 10.3333 WHERE \"UPC\" = '123456789012'"
        )

        payload = {
            "check_number": "CH_RND",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "123456789012", "product_number": 3}],
        }
        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT sum_total, vat FROM \"check\" WHERE check_number = 'CH_RND'"
        )

        # 10.3333 * 3 = 30.9999
        self.assertEqual(float(check["sum_total"]), 30.9999)
        # vat = 30.9999 * 0.2 = 6.19998 (DB Decimal(13,4) will round this strictly to 6.2000)
        self.assertAlmostEqual(float(check["vat"]), 6.2000, places=4)

        # ... попередні методи класу CheckTransactionTests ...

    def test_checkout_ignores_frontend_price_uses_db_price(self):
        """Case 26: Price Update During Checkout. The system must use the real DB price, ignoring frontend payload payload."""
        # Update price in DB right before checkout
        queries.execute(
            "UPDATE store_product SET selling_price = 150.00 WHERE \"UPC\" = '123456789012'"
        )

        payload = {
            "check_number": "CH_PRICE",
            "id_employee": "EMP_TEST",
            "products": [
                # Hacker tries to send a fake low price of 10.00
                {"UPC": "123456789012", "product_number": 2, "selling_price": 10.00}
            ],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT sum_total FROM \"check\" WHERE check_number = 'CH_PRICE'"
        )
        # Real calculation: 150.00 * 2 = 300.00 (MUST NOT BE 20.00)
        self.assertEqual(float(check["sum_total"]), 300.00)

    def test_checkout_with_zero_price_product(self):
        """Case 28: Zero Value Financials. 100% discount should process correctly without VAT calculation errors."""
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('ZERO_UPC', 100, 0.00, 10, FALSE)"""
        )

        payload = {
            "check_number": "CH_ZERO",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "ZERO_UPC", "product_number": 5}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT sum_total, vat FROM \"check\" WHERE check_number = 'CH_ZERO'"
        )
        self.assertEqual(float(check["sum_total"]), 0.00)
        self.assertEqual(float(check["vat"]), 0.00)

    def test_create_check_invalid_card_fails(self):
        """Case 29: Invalid Foreign Key. Creating a check with a non-existent card returns 400 safely."""

        # 1. Очищення БД (якщо це не винесено у метод tearDown/setUp)
        queries.execute('DELETE FROM "check"')
        queries.execute("DELETE FROM store_product")

        # 2. Сетап: Додаємо товар
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
               VALUES ('123456789012', 100, 40.00, 10, FALSE)"""
        )

        # 3. Підготовка даних
        payload = {
            "check_number": "BAD_CHK",
            "id_employee": "EMP_TEST",
            "card_number": "GHOST_CARD",
            "products": [{"UPC": "123456789012", "product_number": 1}],
        }

        # 4. Виконання запиту (ТУТ ДОДАНО json.dumps)
        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )

        # 5. Перевірки
        self.assertEqual(
            response.status_code,
            400,
            f"Очікувався 400 статус, але отримано {response.status_code}. Тіло: {response.content.decode()}"
        )

        check = queries.fetch_one(
            'SELECT * FROM "check" WHERE check_number = %s',
            [payload["check_number"]]
        )
        self.assertIsNone(check)

    def test_massive_payload_handling(self):
        """Case 30: Massive Payload. Check with 100 unique UPCs is processed correctly in a single atomic transaction."""
        # Generate 100 unique store_products dynamically
        for i in range(1, 101):
            upc = f"MASS_{i:03d}"
            queries.execute(
                """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                               VALUES (%s, 100, 10.00, 5, FALSE)""",
                [upc],
            )

        # Create payload with 100 items
        products_payload = [
            {"UPC": f"MASS_{i:03d}", "product_number": 1} for i in range(1, 101)
        ]

        payload = {
            "check_number": "CH_MASSIVE",
            "id_employee": "EMP_TEST",
            "products": products_payload,
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT sum_total, vat FROM \"check\" WHERE check_number = 'CH_MASSIVE'"
        )
        self.assertIsNotNone(check)

        # 100 unique items * 10.00 = 1000.00
        self.assertEqual(float(check["sum_total"]), 1000.00)

        sales_count = queries.fetch_one(
            "SELECT COUNT(*) as count FROM sale WHERE check_number = 'CH_MASSIVE'"
        )
        self.assertEqual(sales_count["count"], 100)


class Case20RaceConditionTests(TransactionTestCase):
    def setUp(self):
        # TransactionTestCase flushes the DB, so we must re-seed constraints and basic data
        call_command("apply_constraints")
        queries.execute(
            "INSERT INTO category (category_number, category_name) VALUES (1, 'Race Category')"
        )
        queries.execute(
            "INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES (100, 1, 'Race Prod', 'X')"
        )
        queries.execute(
            """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code)
                           VALUES ('EMP_RACE', 'Тестер', 'Рейс', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380123456789', 'Київ', 'Вул', '0')"""
        )

        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('RACE_UPC', 100, 50.00, 2, FALSE)"""
        )

    def test_concurrent_purchases_respect_stock(self):
        """Case 20: Race Condition. Two parallel requests try to buy 2 units each, but only 2 exist. FOR UPDATE must block and fail one."""
        results = []

        def make_purchase(check_number):
            try:
                client = Client()
                payload = {
                    "check_number": check_number,
                    "id_employee": "EMP_RACE",
                    "products": [{"UPC": "RACE_UPC", "product_number": 2}],
                }
                res = client.post(
                    "/api/checks/",
                    data=json.dumps(payload),
                    content_type="application/json",
                )
                results.append(res.status_code)
            finally:
                connection.close()

        t1 = threading.Thread(target=make_purchase, args=("CHK_R1",))
        t2 = threading.Thread(target=make_purchase, args=("CHK_R2",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # One transaction gets the lock and succeeds (201), the other waits, sees 0 stock, and fails (400)
        self.assertIn(201, results)
        self.assertIn(400, results)

        # Ensure stock never goes below 0 and is exactly 0 now
        stock = queries.fetch_one(
            "SELECT products_number FROM store_product WHERE \"UPC\" = 'RACE_UPC'"
        )
        self.assertEqual(stock["products_number"], 0)
