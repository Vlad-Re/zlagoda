from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Seeds the database with test data for Zlagoda supermarket"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        with connection.cursor() as cursor:
            # Clear database
            cursor.execute("""
                           TRUNCATE TABLE sale, "check", customer_card, employee,
                               store_product, product, category CASCADE;
                           """)

            # Categories
            cursor.execute(
                "INSERT INTO category (category_number, category_name) VALUES "
                "(1, 'Молочні продукти'), (2, 'Хлібобулочні'), (3, 'М''ясо');"
            )

            # Products
            cursor.execute("""
                           INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES
                                                                                                                (1, 1, 'Молоко 2.5%', 'Пляшка 1л'),
                                                                                                                (2, 1, 'Сир Гауда', 'Ваговий'),
                                                                                                                (3, 2, 'Батон Нарізний', 'Упаковка'),
                                                                                                                (4, 2, 'Хліб Чорний', 'Буханка'),
                                                                                                                (5, 3, 'Ковбаса Лікарська', 'Вагова');
                           """)

            # Store products
            cursor.execute("""
                           INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product) VALUES
                                                                                                                                              ('100000000001', NULL, 1, 35.00, 100, FALSE),
                                                                                                                                              ('100000000002', '100000000001', 1, 28.00, 20, TRUE),
                                                                                                                                              ('200000000001', NULL, 2, 350.00, 10, FALSE),
                                                                                                                                              ('300000000001', NULL, 3, 25.00, 50, FALSE),
                                                                                                                                              ('400000000001', NULL, 4, 30.00, 40, FALSE),
                                                                                                                                              ('500000000001', NULL, 5, 250.00, 15, FALSE);
                           """)

            # Employees
            cursor.execute("""
                           INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code) VALUES
                                                                                                                                                                                  ('EMP01', 'Коваленко', 'Іван', 'Manager', 25000.00, '1985-05-20', '2023-01-10', '+380501111111', 'Київ', 'Хрещатик', '01001'),
                                                                                                                                                                                  ('EMP02', 'Шевченко', 'Анна', 'Cashier', 15000.00, '1998-11-15', '2025-02-01', '+380672222222', 'Київ', 'Поділ', '04071'),
                                                                                                                                                                                  ('EMP03', 'Бойко', 'Олег', 'Cashier', 15000.00, '2000-03-10', '2025-06-15', '+380633333333', 'Київ', 'Оболонь', '04205');
                           """)

            # Customer cards
            cursor.execute("""
                           INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, percent) VALUES
                                                                                                                       ('CARD000000001', 'Мельник', 'Петро', '+380994444444', 5),
                                                                                                                       ('CARD000000002', 'Лисенко', 'Олена', '+380995555555', 10),
                                                                                                                       ('CARD000000003', 'Кравчук', 'Марія', '+380996666666', 15);
                           """)

            # Checks
            checks_data = [
                ("CH26010100", "EMP02", "CARD000000001", "2026-01-05 10:15:00"),
                ("CH26010200", "EMP02", "CARD000000002", "2026-01-10 12:30:00"),
                ("CH26010300", "EMP02", "CARD000000003", "2026-01-15 14:45:00"),
                ("CH26020400", "EMP02", "CARD000000001", "2026-02-20 09:10:00"),
                ("CH26020500", "EMP02", None, "2026-02-25 18:20:00"),
                ("CH26030600", "EMP02", "CARD000000002", "2026-03-05 11:11:00"),
                ("CH26030700", "EMP03", "CARD000000001", "2026-03-12 16:40:00"),
                ("CH26030800", "EMP03", None, "2026-03-20 19:55:00"),
            ]

            for ch_num, emp, card, date in checks_data:
                cursor.execute(
                    """
                               INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                               VALUES (%s, %s, %s, %s, 100.00, 20.00);
                               """,
                    [ch_num, emp, card, date],
                )

            # Sales
            sales_data = [
                ("100000000001", "CH26010100", 2, 35.00),
                ("300000000001", "CH26010100", 1, 25.00),
                ("200000000001", "CH26010200", 1, 350.00),
                ("100000000002", "CH26010300", 3, 28.00),
                ("400000000001", "CH26020400", 2, 30.00),
                ("500000000001", "CH26020500", 1, 250.00),
                ("100000000001", "CH26030600", 1, 35.00),
                ("300000000001", "CH26030700", 2, 25.00),
                ("400000000001", "CH26030800", 1, 30.00),
            ]

            for upc, ch_num, qty, price in sales_data:
                cursor.execute(
                    """
                               INSERT INTO sale ("UPC", check_number, product_number, selling_price)
                               VALUES (%s, %s, %s, %s);
                               """,
                    [upc, ch_num, qty, price],
                )

                cursor.execute(
                    """
                               UPDATE "check"
                               SET sum_total = (SELECT COALESCE(SUM(product_number * selling_price), 0) FROM sale WHERE check_number = %s),
                                   vat = (SELECT COALESCE(SUM(product_number * selling_price), 0) * 0.2 FROM sale WHERE check_number = %s)
                               WHERE check_number = %s;
                               """,
                    [ch_num, ch_num, ch_num],
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded the database!"))
