import json
import datetime
from datetime import date

from core import queries
from .test_base import BaseZlagodaTest


class ApiCrudTests(BaseZlagodaTest):
    def test_get_categories(self):
        """Test getting the list of categories."""
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data["results"]) >= 1)
        self.assertEqual(data["results"][0]["category_name"], "Тестова категорія")

    def test_create_employee_under_18_fails(self):
        """Test semantic constraint chk_emp_age (employee < 18 years)."""
        payload = {
            "id_employee": "EMP_YOUTH",
            "empl_surname": "Молодий",
            "empl_name": "Петро",
            "empl_role": "Cashier",
            "salary": 10000,
            "date_of_birth": "2020-01-01",  # Obviously less than 18 years
            "date_of_start": "2026-06-15",
            "phone_number": "+380123456789",
            "city": "Київ",
            "street": "Вулиця",
            "zip_code": "00000",
            "password_hash": "",
        }

        response = self.client.post(
            "/api/employees/", data=json.dumps(payload), content_type="application/json"
        )

        # Expect 400 Bad Request, since DB constraint will reject the record
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Constraint violation", data["error"])

    # ==========================================
    # КЕЙС 1: Категорія без товарів
    # ==========================================
    def test_delete_empty_category_success(self):
        """Успішне видалення порожньої категорії."""
        queries.execute(
            "INSERT INTO category (category_number, category_name) VALUES (99, 'Порожня категорія')"
        )
        response = self.client.delete("/api/categories/99/")
        self.assertEqual(response.status_code, 200)

        cat = queries.fetch_one("SELECT * FROM category WHERE category_number = 99")
        self.assertIsNone(cat)

    def test_delete_category_with_products_fails(self):
        """Помилка 409: Спроба видалити категорію, до якої прив'язані товари."""
        # Категорія 1 і товар 100 вже створені у test_base.py
        response = self.client.delete("/api/categories/1/")
        self.assertEqual(response.status_code, 409)

    # ==========================================
    # КЕЙС 2: Товари, які не продавалися
    # ==========================================
    def test_delete_unsold_store_product_success(self):
        """Успішне видалення товару з вітрини, якщо його немає в жодному чеку."""
        queries.execute(
            "INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES (101, 1, 'Новий', 'Опис')"
        )
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('UNSOLD123', 101, 10.0, 5, FALSE)"""
        )
        response = self.client.delete("/api/store-products/UNSOLD123/")
        self.assertEqual(response.status_code, 200)

    def test_delete_sold_store_product_fails(self):
        """Помилка 409: Спроба видалити з вітрини товар, який вже пробито в чеку."""
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat)
                           VALUES ('CH_TEST_1', 'EMP_TEST', '2026-06-16', 10.0, 2.0)"""
        )
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('SOLD123', 100, 10.0, 5, FALSE)"""
        )
        queries.execute(
            """INSERT INTO sale ("UPC", check_number, product_number, selling_price)
                           VALUES ('SOLD123', 'CH_TEST_1', 1, 10.0)"""
        )

        response = self.client.delete("/api/store-products/SOLD123/")
        self.assertEqual(response.status_code, 409)

    # ==========================================
    # КЕЙС 3: Касир-новачок
    # ==========================================
    def test_delete_rookie_cashier_success(self):
        """Успішне видалення касира, який не пробив жодного чека."""
        queries.execute(
            """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
                           VALUES ('ROOKIE', 'Новачок', 'Іван', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380000000000', 'Київ', 'Вул', '00000', %s)""",
            ['']
        )
        response = self.client.delete("/api/employees/ROOKIE/")
        self.assertEqual(response.status_code, 200)

    def test_delete_cashier_with_checks_fails(self):
        """Помилка 409: Спроба видалити касира, в якого є історія чеків."""
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat)
                           VALUES ('CH_EMP_1', 'EMP_TEST', '2026-06-16', 10.0, 2.0)"""
        )
        response = self.client.delete("/api/employees/EMP_TEST/")
        self.assertEqual(response.status_code, 409)

    # ==========================================
    # КЕЙС 4: Невикористані картки клієнтів (Сплячі)
    # ==========================================
    def test_delete_unused_card_success(self):
        """Успішне видалення картки клієнта, якщо за нею не було покупок."""
        queries.execute(
            """INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, percent)
                           VALUES ('CARD_SLP', 'Сплячий', 'Клієнт', '+380111111111', 5)"""
        )
        response = self.client.delete("/api/customer-cards/CARD_SLP/")
        self.assertEqual(response.status_code, 200)

    def test_delete_used_card_fails(self):
        """Помилка 400: Спроба видалити картку, яка прив'язана до чека."""
        queries.execute(
            """INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, percent)
                           VALUES ('CARD_ACT', 'Активний', 'Клієнт', '+380111111112', 5)"""
        )
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                           VALUES ('CH_CARD_1', 'EMP_TEST', 'CARD_ACT', '2026-06-16', 10.0, 2.0)"""
        )

        response = self.client.delete("/api/customer-cards/CARD_ACT/")
        self.assertEqual(response.status_code, 400)

    def test_create_product_invalid_category_fails(self):
        """Case 29: Invalid Foreign Key. Creating a product with a non-existent category returns 400."""
        payload = {
            "id_product": 999,
            "category_number": 99999,  # Does not exist in DB
            "product_name": "Ghost Product",
            "characteristics": "None",
        }

        response = self.client.post(
            "/api/products/", data=json.dumps(payload), content_type="application/json"
        )
        # IntegrityError (due to invalid foreign key) should be caught and returned as 400 Bad Request.
        self.assertEqual(response.status_code, 400)


class Case12PromotionalTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute("DELETE FROM store_product")
        # Base product
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('BASE_UPC', 100, 100.00, 50, FALSE)"""
        )
        # Promo product pointing to base
        queries.execute(
            """INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product)
                           VALUES ('PROM_UPC', 'BASE_UPC', 100, 80.00, 20, TRUE)"""
        )

    def test_filter_promotional_products(self):
        """Case 12: Verify endpoint correctly filters promotional products."""
        response = self.client.get("/api/store-products/?promotional=true")
        data = json.loads(response.content)["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["UPC"], "PROM_UPC")
        self.assertTrue(data[0]["promotional_product"])

    def test_filter_non_promotional_products(self):
        """Case 12: Verify endpoint correctly filters non-promotional products."""
        response = self.client.get("/api/store-products/?promotional=false")
        data = json.loads(response.content)["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["UPC"], "BASE_UPC")
        self.assertFalse(data[0]["promotional_product"])


class Case13NullAddressTests(BaseZlagodaTest):
    def test_create_customer_without_address(self):
        """Case 13: Customer cards can be created and retrieved with NULL address details."""
        payload = {
            "card_number": "CARD_NO_ADR",
            "cust_surname": "Бездомний",
            "cust_name": "Олег",
            "phone_number": "+380000000000",
            "percent": 3,
            # explicitly omitting city, street, zip_code
        }

        response = self.client.post(
            "/api/customer-cards/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        response_get = self.client.get("/api/customer-cards/CARD_NO_ADR/")
        data = json.loads(response_get.content)

        self.assertIsNone(data.get("city"))
        self.assertIsNone(data.get("street"))
        self.assertIsNone(data.get("zip_code"))


class Case15TransactionBurstTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute('DELETE FROM "check"')

        # Insert checks with exactly the same date but progressing seconds
        burst_data = [
            ("CH_B1", "2026-06-16 12:00:01"),
            ("CH_B2", "2026-06-16 12:00:02"),
            ("CH_B3", "2026-06-16 12:00:03"),
        ]
        for chk_id, time_str in burst_data:
            queries.execute(
                'INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat) VALUES (%s, %s, %s, %s, %s)',
                [chk_id, "EMP_TEST", time_str, 100, 20],
            )

    def test_checks_sorted_by_date_desc(self):
        """Case 15: High density checks should be sorted strictly by print_date DESC."""
        response = self.client.get("/api/checks/")
        data = json.loads(response.content)["results"]

        # Order should be newest to oldest: B3 -> B2 -> B1
        self.assertEqual(data[0]["check_number"], "CH_B3")
        self.assertEqual(data[1]["check_number"], "CH_B2")
        self.assertEqual(data[2]["check_number"], "CH_B1")


class Case16PromoCascadeTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute("DELETE FROM store_product")
        # Create base product
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('BASE_16', 100, 100.00, 50, FALSE)"""
        )
        # Create promo product pointing to base
        queries.execute(
            """INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product)
                           VALUES ('PROM_16', 'BASE_16', 100, 80.00, 20, TRUE)"""
        )

    def test_delete_base_sets_promo_fk_to_null(self):
        """Case 16: Deleting a base product should set UPC_prom to NULL in the promotional product, keeping it intact."""
        response = self.client.delete("/api/store-products/BASE_16/")
        self.assertEqual(response.status_code, 200)

        # Promo product should still exist, but UPC_prom must be NULL
        promo_prod = queries.fetch_one(
            "SELECT * FROM store_product WHERE \"UPC\" = 'PROM_16'"
        )
        self.assertIsNotNone(promo_prod)
        self.assertIsNone(promo_prod["UPC_prom"])


class Case19BoundaryAgeTests(BaseZlagodaTest):
    def get_exact_18_date(self):
        today = date.today()
        try:
            return today.replace(year=today.year - 18)
        except ValueError:
            return today.replace(year=today.year - 18, month=2, day=28)

    def test_create_employee_exactly_18_success(self):
        """Case 19: Employee exactly 18 years old today should be accepted by the DB."""
        exact_18 = self.get_exact_18_date().strftime("%Y-%m-%d")
        payload = {
            "id_employee": "EMP_18",
            "empl_surname": "Володимиров",
            "empl_name": "Володимир",
            "empl_role": "Cashier",
            "salary": 15000,
            "date_of_birth": exact_18,
            "date_of_start": "2026-06-16",
            "phone_number": "+380000000018",
            "city": "Київ",
            "street": "Вулиця",
            "zip_code": "00000",
            "password_hash": "",
        }

        response = self.client.post(
            "/api/employees/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

    def test_create_employee_under_18_by_one_day_fails(self):
        """Case 19: Employee who turns 18 tomorrow should be rejected today."""
        under_18 = (self.get_exact_18_date() + datetime.timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )
        payload = {
            "id_employee": "EMP_17",
            "empl_surname": "Молодий",
            "empl_name": "Олег",
            "empl_role": "Cashier",
            "salary": 15000,
            "date_of_birth": under_18,
            "date_of_start": "2026-06-16",
            "phone_number": "+380000000017",
            "city": "Київ",
            "street": "Вулиця",
            "zip_code": "00000",
            "password_hash": "",
        }

        response = self.client.post(
            "/api/employees/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


# ... попередні класи в test_api.py ...


class Case22PhoneBoundaryTests(BaseZlagodaTest):
    def test_phone_length_13_success(self):
        """Case 22: Phone with exactly 13 characters (+ and 12 digits) is accepted."""
        payload = {
            "id_employee": "EMP_PHN1",
            "empl_surname": "Тестер",
            "empl_name": "Телефон",
            "empl_role": "Cashier",
            "salary": 15000,
            "date_of_birth": "1990-01-01",
            "date_of_start": "2026-06-16",
            "phone_number": "+380123456789",  # 13 symbols
            "city": "К",
            "street": "В",
            "zip_code": "0",
            "password_hash": "",
        }
        response = self.client.post(
            "/api/employees/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

    def test_phone_length_14_fails(self):
        """Case 22: Phone with 14 characters is rejected by DB constraint LENGTH(phone_number) <= 13."""
        payload = {
            "id_employee": "EMP_PHN2",
            "empl_surname": "Тестер",
            "empl_name": "Телефон",
            "empl_role": "Cashier",
            "salary": 15000,
            "date_of_birth": "1990-01-01",
            "date_of_start": "2026-06-16",
            "phone_number": "+3801234567890",  # 14 symbols
            "city": "К",
            "street": "В",
            "zip_code": "0",
            "password_hash": "",
        }
        response = self.client.post(
            "/api/employees/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


class Case24CheckDeleteCascadeTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute('DELETE FROM "check"')
        queries.execute("DELETE FROM store_product")
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('UPC_DEL', 100, 10, 10, FALSE)"""
        )
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat)
                           VALUES ('CH_DEL', 'EMP_TEST', '2026-06-16', 10, 2)"""
        )
        queries.execute(
            """INSERT INTO sale ("UPC", check_number, product_number, selling_price)
                           VALUES ('UPC_DEL', 'CH_DEL', 1, 10)"""
        )

    def test_delete_check_cascades_to_sales(self):
        """Case 24: Deleting a check automatically deletes associated sales via ON DELETE CASCADE."""
        sales_before = queries.fetch_all(
            "SELECT * FROM sale WHERE check_number = 'CH_DEL'"
        )
        self.assertEqual(len(sales_before), 1)

        response = self.client.delete("/api/checks/CH_DEL/")
        self.assertEqual(response.status_code, 200)

        # Sales must be wiped out automatically
        sales_after = queries.fetch_all(
            "SELECT * FROM sale WHERE check_number = 'CH_DEL'"
        )
        self.assertEqual(len(sales_after), 0)


class Case25SelfReferentialPromoTests(BaseZlagodaTest):
    def test_self_referential_promo_fails(self):
        """Case 25: A product cannot be its own promotional counterpart."""
        queries.execute("DELETE FROM store_product")
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('UPC_LOOP', 100, 10, 10, FALSE)"""
        )

        payload = {
            "UPC_prom": "UPC_LOOP",  # Points to itself!
            "id_product": 100,
            "selling_price": 8,
            "products_number": 10,
            "promotional_product": True,
        }

        response = self.client.put(
            "/api/store-products/UPC_LOOP/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
