import json
from core import queries
from .test_base import BaseZlagodaTest


class ReportTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        session = self.client.session
        session["employee_id"] = "EMP_TEST"
        session["role"] = "Manager"
        session.save()

    def test_ui_dropdowns_endpoint(self):
        """Test auxiliary endpoint for forming dropdown lists."""
        response = self.client.get("/api/ui/dropdowns/categories/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("id", data["results"][0])
        self.assertIn("name", data["results"][0])


class Case5RelationalDivisionTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        session = self.client.session
        session["employee_id"] = "EMP_TEST"
        session["role"] = "Manager"
        session.save()

        queries.execute('DELETE FROM "check"')

        # Створюємо 2 обов'язкові картки
        queries.execute(
            """INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, percent)
                           VALUES ('C1', 'Клієнт1', 'А', '+380001', 5),
                                  ('C2', 'Клієнт2', 'Б', '+380002', 5)"""
        )

        # Створюємо касира-зірку і касира-аутсайдера
        queries.execute(
            """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
               VALUES ('STAR', 'Зірка', 'З', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380003', 'К', 'В', '0', ''),
                      ('LAZY', 'Лінивий', 'Л', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380004', 'К', 'В', '0', '')"""
        )

        # STAR обслуговує ОБОХ клієнтів (умови реляційного ділення виконані)
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                           VALUES ('CH1', 'STAR', 'C1', '2026-06-16', 10, 2),
                                  ('CH2', 'STAR', 'C2', '2026-06-16', 10, 2)"""
        )

        # LAZY обслуговує ТІЛЬКИ одного клієнта (не підпадає під умову)
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                           VALUES ('CH3', 'LAZY', 'C1', '2026-06-16', 10, 2)"""
        )

    def test_employee_served_all_customers_included(self):
        """Звіт ПОВИНЕН містити касира, який пробив чеки для всіх існуючих карток."""
        response = self.client.get("/api/reports/employees-served-all-customers/")
        data = json.loads(response.content)["results"]
        surnames = [e["empl_surname"] for e in data]

        self.assertIn("Зірка", surnames)

    def test_employee_missed_one_customer_excluded(self):
        """Звіт НЕ ПОВИНЕН містити касира, який пропустив хоча б одну картку."""
        response = self.client.get("/api/reports/employees-served-all-customers/")
        data = json.loads(response.content)["results"]
        surnames = [e["empl_surname"] for e in data]

        self.assertNotIn("Лінивий", surnames)

    def test_new_customer_invalidates_all_employees(self):
        """Якщо з'являється новий клієнт без покупок, жоден касир більше не відповідає умові 'обслужив усіх'."""
        queries.execute(
            """INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, percent)
                           VALUES ('C3', 'Новачок', 'В', '+380005', 5)"""
        )

        response = self.client.get("/api/reports/employees-served-all-customers/")
        data = json.loads(response.content)["results"]

        # Тепер список має бути порожнім, бо ні Зірка, ні Лінивий не обслуговували 'C3'
        self.assertEqual(len(data), 0)


class Case6CustomerServedByAllTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()

        queries.execute("DELETE FROM sale")
        queries.execute('DELETE FROM "check"')
        queries.execute("DELETE FROM customer_card")

        queries.execute("DELETE FROM employee WHERE id_employee != 'EMP_TEST'")

        queries.execute(
            """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
               VALUES ('CASH1', 'Касир1', 'А', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380001', 'К', 'В', '0', ''),
                      ('CASH2', 'Касир2', 'Б', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380002', 'К', 'В', '0', '')"""
        )

        queries.execute(
            """INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, percent)
               VALUES ('CARD_ALL', 'Улюбленець', 'У', '+380003', 5),
                      ('CARD_SOME', 'Випадковий', 'В', '+380004', 5)"""
        )

        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
               VALUES ('CH1', 'CASH1', 'CARD_ALL', '2026-06-16', 10, 2),
                      ('CH2', 'CASH2', 'CARD_ALL', '2026-06-16', 10, 2),
                      ('CH_EMP', 'EMP_TEST', 'CARD_ALL', '2026-06-16', 10, 2)"""
        )

        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
               VALUES ('CH3', 'CASH1', 'CARD_SOME', '2026-06-16', 10, 2)"""
        )

    def test_customer_served_by_all_included(self):
        """Case 6: Customer served by every single cashier should be in the report."""
        response = self.client.get("/api/reports/customers-served-by-all-cashiers/")
        data = json.loads(response.content)["results"]
        surnames = [c["cust_surname"] for c in data]

        self.assertIn("Улюбленець", surnames)

    def test_customer_missed_cashier_excluded(self):
        """Case 6: Customer who missed at least one cashier should NOT be in the report."""
        response = self.client.get("/api/reports/customers-served-by-all-cashiers/")
        data = json.loads(response.content)["results"]
        surnames = [c["cust_surname"] for c in data]

        self.assertNotIn("Випадковий", surnames)


class Case7And8CategoryProductsTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute('DELETE FROM "check"')
        queries.execute("DELETE FROM store_product")
        queries.execute("DELETE FROM product")
        queries.execute("DELETE FROM category")

        # Create categories
        queries.execute(
            "INSERT INTO category (category_number, category_name) VALUES (10, 'AllSold'), (20, 'HasDead')"
        )

        # Create products
        queries.execute(
            """INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES
                                                                                                                (101, 10, 'Prod101', 'Х'), (102, 10, 'Prod102', 'Х'),
                                                                                                                (201, 20, 'Prod201', 'Х'), (202, 20, 'Prod202', 'Х')"""
        )

        # Put them in store
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product) VALUES
                                                                                                                                  ('UPC101', 101, 10, 5, FALSE), ('UPC102', 102, 10, 5, FALSE),
                                                                                                                                  ('UPC201', 201, 10, 5, FALSE), ('UPC202', 202, 10, 5, FALSE)"""
        )

        # Sell 101, 102, 201. Leave 202 as DEAD.
        queries.execute(
            """INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat)
                           VALUES ('CH_CAT', 'EMP_TEST', '2026-06-16', 30, 6)"""
        )
        queries.execute(
            """INSERT INTO sale ("UPC", check_number, product_number, selling_price) VALUES
                                                                                                     ('UPC101', 'CH_CAT', 1, 10), ('UPC102', 'CH_CAT', 1, 10), ('UPC201', 'CH_CAT', 1, 10)"""
        )

    def test_category_with_no_dead_products_included(self):
        """Case 7: Category where EVERY product was sold at least once is included."""
        response = self.client.get("/api/reports/categories-all-products-sold/")
        data = json.loads(response.content)["results"]
        cat_names = [c["category_name"] for c in data]
        self.assertIn("AllSold", cat_names)

    def test_category_with_dead_product_excluded(self):
        """Case 8: Category with at least one NEVER sold product is excluded."""
        response = self.client.get("/api/reports/categories-all-products-sold/")
        data = json.loads(response.content)["results"]
        cat_names = [c["category_name"] for c in data]
        self.assertNotIn("HasDead", cat_names)


class Case9TopCashiersTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute('DELETE FROM "check"')
        queries.execute("DELETE FROM store_product")

        # Setup cashiers
        queries.execute(
            """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
               VALUES ('TOP_A', 'Абсолют', 'А', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380001', 'К', 'В', '0', ''),
                      ('TOP_B', 'Богатир', 'Б', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380002', 'К', 'В', '0', ''),
                      ('LAZY_R', 'МалоЧеків', 'М', 'Cashier', 10000, '2000-01-01', '2026-01-01', '+380003', 'К', 'В', '0', '')"""
        )

        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
                           VALUES ('UPC1', 100, 100, 1000, FALSE)"""
        )

        # Generate checks dynamically
        # TOP_A: 6 checks x 1 qty x 100 price = 600 revenue
        for i in range(1, 7):
            chk_id = f"CH_A_{i}"
            queries.execute(
                'INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat) VALUES (%s, %s, %s, %s, %s)',
                [chk_id, "TOP_A", "2026-06-16", 100, 20],
            )
            queries.execute(
                'INSERT INTO sale ("UPC", check_number, product_number, selling_price) VALUES (%s, %s, %s, %s)',
                ["UPC1", chk_id, 1, 100],
            )

        # TOP_B: 6 checks x 2 qty x 100 price = 1200 revenue
        for i in range(1, 7):
            chk_id = f"CH_B_{i}"
            queries.execute(
                'INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat) VALUES (%s, %s, %s, %s, %s)',
                [chk_id, "TOP_B", "2026-06-16", 200, 40],
            )
            queries.execute(
                'INSERT INTO sale ("UPC", check_number, product_number, selling_price) VALUES (%s, %s, %s, %s)',
                ["UPC1", chk_id, 2, 100],
            )

        # LAZY_R: 4 checks x 10 qty x 100 price = 4000 revenue (HIGH revenue, but <= 5 checks)
        for i in range(1, 5):
            chk_id = f"CH_R_{i}"
            queries.execute(
                'INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat) VALUES (%s, %s, %s, %s, %s)',
                [chk_id, "LAZY_R", "2026-06-16", 1000, 200],
            )
            queries.execute(
                'INSERT INTO sale ("UPC", check_number, product_number, selling_price) VALUES (%s, %s, %s, %s)',
                ["UPC1", chk_id, 10, 100],
            )

    def test_top_cashiers_order_and_filter(self):
        """Case 9: Cashiers with <= 5 checks are excluded, remaining sorted by revenue DESC."""
        response = self.client.get("/api/reports/top-cashiers/")
        data = json.loads(response.content)["results"]

        # LAZY_R has max revenue but only 4 checks, must be excluded
        surnames = [c["empl_surname"] for c in data]
        self.assertNotIn("МалоЧеків", surnames)

        # Check order: TOP_B (1200) should be before TOP_A (600)
        self.assertEqual(data[0]["empl_surname"], "Богатир")
        self.assertEqual(data[1]["empl_surname"], "Абсолют")


class Case10PeriodsTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute('DELETE FROM "check"')
        # Create checks spread across the year
        checks = [
            ("CH_JAN", "2026-01-15 10:00:00", 100),
            ("CH_MAY1", "2026-05-10 12:00:00", 200),
            ("CH_MAY2", "2026-05-20 14:00:00", 300),
            ("CH_DEC", "2026-12-01 16:00:00", 500),
        ]
        for chk_id, date, sum_tot in checks:
            queries.execute(
                'INSERT INTO "check" (check_number, id_employee, print_date, sum_total, vat) VALUES (%s, %s, %s, %s, %s)',
                [chk_id, "EMP_TEST", date, sum_tot, sum_tot * 0.2],
            )

    def test_sales_revenue_period_filter(self):
        """Case 10: Date filters should correctly isolate a specific time period without empty tables or bleeding data."""
        # Query only May
        response = self.client.get(
            "/api/reports/sales-revenue/?start=2026-05-01&end=2026-05-31"
        )
        data = json.loads(response.content)

        # Should sum only CH_MAY1 (200) + CH_MAY2 (300) = 500
        self.assertEqual(float(data["total_revenue"]), 500.00)

    def test_sales_revenue_empty_period(self):
        """Case 10: Querying a period with no transactions should safely return 0."""
        response = self.client.get(
            "/api/reports/sales-revenue/?start=2026-03-01&end=2026-03-31"
        )
        data = json.loads(response.content)

        self.assertEqual(float(data["total_revenue"]), 0)
