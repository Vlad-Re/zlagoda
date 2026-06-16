import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = "Generates a massive, representative, algorithmic dataset for Zlagoda"

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating massive dataset with edge-cases...")

        # Fixed seed for predictable but random-looking data
        random.seed(42)

        with connection.cursor() as cursor:
            cursor.execute("""
                           TRUNCATE TABLE sale, "check", customer_card, employee,
                               store_product, product, category CASCADE;
                           """)

            # 1. Categories (10)
            # Category 10 is intentionally empty (Safe Deletion Test)
            categories = [
                (1, "Dairy"),
                (2, "Bakery"),
                (3, "Meat"),
                (4, "Beverages"),
                (5, "Snacks"),
                (6, "Fruits"),
                (7, "Vegetables"),
                (8, "Seafood"),
                (9, "Frozen"),
                (10, "Empty Category (For Deletion Test)"),
            ]
            cursor.executemany(
                "INSERT INTO category (category_number, category_name) VALUES (%s, %s)",
                categories,
            )

            # 2. Products (50)
            products = []
            for i in range(1, 51):
                if i in [49, 50]:
                    cat = 9
                else:
                    cat = random.randint(1, 8)
                products.append((i, cat, f"Product_{i}", f"Characteristics_{i}"))
            cursor.executemany(
                "INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES (%s, %s, %s, %s)",
                products,
            )

            # 3. Store Products (80)
            store_products = []
            upc_list = []
            for i in range(1, 61):
                upc = f"{i:012d}"
                upc_list.append(upc)
                price = round(random.uniform(15.0, 500.0), 2)
                # 20% chance of 0 stock for Out-Of-Stock testing
                qty = random.choice([0, 0, 10, 50, 100, 200])
                store_products.append(
                    (
                        upc,
                        None,
                        i if i <= 50 else random.randint(1, 49),
                        price,
                        qty,
                        False,
                    )
                )

            # Add 20 promotional products linked to base products
            for i in range(61, 81):
                upc = f"{i:012d}"
                upc_list.append(upc)
                base_upc = f"{i-60:012d}"
                base_price = next(sp[3] for sp in store_products if sp[0] == base_upc)
                promo_price = round(base_price * 0.8, 2)
                store_products.append(
                    (upc, base_upc, i - 60, promo_price, random.randint(10, 50), True)
                )

            cursor.executemany(
                """
                               INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               """,
                store_products,
            )

            # 4. Employees (10) — password = id_employee (e.g. EMP01)
            # EMP10 has 0 checks (Safe Deletion Test)
            employees = []
            roles = ["Manager", "Manager"] + ["Cashier"] * 8
            cashier_ids = []
            for i in range(1, 11):
                emp_id = f"EMP{i:02d}"
                if roles[i - 1] == "Cashier":
                    cashier_ids.append(emp_id)
                employees.append(
                    (
                        emp_id,
                        f"Surname_{i}",
                        f"Name_{i}",
                        roles[i - 1],
                        15000.0 + random.randint(0, 5000),
                        "1995-01-01",
                        "2023-01-01",
                        f"+38099{i:07d}",
                        "Kyiv",
                        f"Street {i}",
                        f"010{i:02d}",
                        make_password(emp_id),
                    )
                )
            cursor.executemany(
                """
                               INSERT INTO employee (id_employee, empl_surname, empl_name, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               """,
                employees,
            )

            # 5. Customer Cards (30)
            cards = []
            card_ids = []
            for i in range(1, 31):
                card_id = f"CARD{i:09d}"
                card_ids.append(card_id)
                pct = random.choice([0, 5, 10, 15, 20])
                has_address = random.choice([True, False])
                cards.append(
                    (
                        card_id,
                        f"Cust_Sur_{i}",
                        f"Cust_Name_{i}",
                        f"+38050{i:07d}",
                        "Lviv" if has_address else None,
                        f"Avenue {i}" if has_address else None,
                        f"790{i:02d}" if has_address else None,
                        pct,
                    )
                )
            cursor.executemany(
                """
                               INSERT INTO customer_card (card_number, cust_surname, cust_name, phone_number, city, street, zip_code, percent)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                               """,
                cards,
            )

            # 6. Checks (500) and Sales (approx. 1500)
            start_date = datetime(2025, 12, 1)
            time_between_dates = datetime(2026, 6, 15) - start_date

            active_cashiers = cashier_ids[:-1]  # EMP10 excluded (0 checks)
            available_upcs = [
                u for u in upc_list if not u.endswith("49") and not u.endswith("50")
            ]

            active_cards = card_ids[:-5]
            inactive_cards = card_ids[-5:]

            checks = []
            sales = []

            burst_time = datetime(2026, 6, 14, 18, 0, 0)
            for i in range(10):
                ch_num = f"CH_BRST_{i:02d}"
                print_date = burst_time + timedelta(seconds=(45 * i))
                checks.append(
                    (
                        ch_num,
                        "EMP02",
                        None,
                        print_date.strftime("%Y-%m-%d %H:%M:%S"),
                        0,
                        0,
                    )
                )
                sales.append((available_upcs[0], ch_num, 1, store_products[0][3]))

            for i in range(1, 501):
                ch_num = f"CH{i:08d}"
                emp = random.choice(active_cashiers)
                card = random.choice(active_cards + [None])

                # EDGE CASE 1: EMP03 serves ALL active customers (for relational division)
                if i <= len(active_cards):
                    emp = "EMP03"
                    card = active_cards[i - 1]

                # EDGE CASE 2: CARD001 is served by ALL active cashiers
                if len(active_cards) < i <= len(active_cards) + len(active_cashiers):
                    emp = active_cashiers[i - len(active_cards) - 1]
                    card = active_cards[0]

                random_days = random.randrange(time_between_dates.days)
                random_seconds = random.randrange(86400)
                print_date = start_date + timedelta(
                    days=random_days, seconds=random_seconds
                )

                checks.append(
                    (ch_num, emp, card, print_date.strftime("%Y-%m-%d %H:%M:%S"), 0, 0)
                )

                # Generate Sales for this check
                num_items = random.randint(1, 5)
                chosen_upcs = random.sample(available_upcs, num_items)
                for upc in chosen_upcs:
                    price = next(sp[3] for sp in store_products if sp[0] == upc)
                    sales.append((upc, ch_num, random.randint(1, 3), price))

            cursor.executemany(
                """
                               INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               """,
                checks,
            )

            cursor.executemany(
                """
                               INSERT INTO sale ("UPC", check_number, product_number, selling_price)
                               VALUES (%s, %s, %s, %s)
                               """,
                sales,
            )

            # 7. Dynamic Total Calculation
            cursor.execute("""
                           UPDATE "check"
                           SET sum_total = COALESCE((SELECT SUM(product_number * selling_price) FROM sale WHERE sale.check_number = "check".check_number), 0),
                               vat = COALESCE((SELECT SUM(product_number * selling_price) * 0.2 FROM sale WHERE sale.check_number = "check".check_number), 0);
                           """)

        self.stdout.write(
            self.style.SUCCESS(
                f"Success! Generated 10 categories, 50 products, 80 store products, 10 employees, 30 cards, 500 checks, and {len(sales)} sales."
            )
        )
