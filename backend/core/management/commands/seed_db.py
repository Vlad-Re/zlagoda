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
                (1, "Молочні продукти"),
                (2, "Хлібобулочні вироби"),
                (3, "М'ясо"),
                (4, "Напої"),
                (5, "Снеки"),
                (6, "Фрукти"),
                (7, "Овочі"),
                (8, "Морепродукти"),
                (9, "Заморожені продукти"),
                (10, "Порожня категорія (для тесту видалення)"),
            ]
            cursor.executemany(
                "INSERT INTO category (category_number, category_name) VALUES (%s, %s)",
                categories,
            )

            # 2. Products (50) — realistic names; categories match the names.
            # Products 49 & 50 are kept in category 9 (their UPCs are never sold).
            products = [
                (1, 1, "Молоко 2.5%", "Пастеризоване, 1 л"),
                (2, 1, "Кефір 1%", "900 мл"),
                (3, 1, "Сметана 20%", "400 г"),
                (4, 1, "Сир кисломолочний 9%", "350 г"),
                (5, 1, "Масло вершкове 82%", "200 г"),
                (6, 1, "Йогурт натуральний", "Без додатків, 300 г"),
                (7, 1, "Сир твердий", "Голландський, 45%, 200 г"),
                (8, 2, "Хліб пшеничний", "Нарізний, 500 г"),
                (9, 2, "Батон молочний", "400 г"),
                (10, 2, "Багет французький", "250 г"),
                (11, 2, "Булочка з маком", "80 г"),
                (12, 2, "Лаваш тонкий", "200 г"),
                (13, 3, "Філе куряче", "Охолоджене, 1 кг"),
                (14, 3, "Свинина (шийка)", "1 кг"),
                (15, 3, "Яловичина (вирізка)", "1 кг"),
                (16, 3, "Фарш домашній", "500 г"),
                (17, 3, "Ковбаса варена", "Лікарська, 450 г"),
                (18, 3, "Сосиски молочні", "400 г"),
                (19, 4, "Сік яблучний", "1 л"),
                (20, 4, "Вода мінеральна газована", "1.5 л"),
                (21, 4, "Чай чорний", "25 пакетиків"),
                (22, 4, "Кава мелена", "250 г"),
                (23, 4, "Лимонад", "0.5 л"),
                (24, 4, "Вода питна негазована", "1.5 л"),
                (25, 5, "Чіпси картопляні", "Зі сметаною, 130 г"),
                (26, 5, "Сухарики житні", "100 г"),
                (27, 5, "Горіхи смажені", "150 г"),
                (28, 5, "Печиво вівсяне", "300 г"),
                (29, 5, "Шоколад молочний", "90 г"),
                (30, 5, "Зефір ванільний", "250 г"),
                (31, 6, 'Яблука "Голден"', "1 кг"),
                (32, 6, "Банани", "1 кг"),
                (33, 6, "Апельсини", "1 кг"),
                (34, 6, "Виноград", "1 кг"),
                (35, 6, "Груші", "1 кг"),
                (36, 7, "Картопля", "1 кг"),
                (37, 7, "Морква", "1 кг"),
                (38, 7, "Цибуля ріпчаста", "1 кг"),
                (39, 7, "Помідори", "1 кг"),
                (40, 7, "Огірки", "1 кг"),
                (41, 8, "Філе оселедця", "У маслі, 300 г"),
                (42, 8, "Креветки варено-морожені", "500 г"),
                (43, 8, "Лосось слабосолоний", "200 г"),
                (44, 8, "Кальмари", "400 г"),
                (45, 8, "Скумбрія копчена", "350 г"),
                (46, 4, "Енергетичний напій", "0.5 л"),
                (47, 5, "Крекери солоні", "180 г"),
                (48, 1, "Ряжанка 4%", "450 мл"),
                (49, 9, "Пельмені заморожені", "Сибірські, 1 кг"),
                (50, 9, "Морозиво пломбір", "Ескімо, 80 г"),
            ]
            cursor.executemany(
                "INSERT INTO product (id_product, category_number, product_name, characteristics) VALUES (%s, %s, %s, %s)",
                products,
            )

            # Realistic selling price (грн) per product id — keeps the shop credible.
            product_prices = {
                1: 42.50, 2: 38.90, 3: 55.00, 4: 78.00, 5: 95.50, 6: 29.90, 7: 165.00,
                8: 28.00, 9: 24.50, 10: 32.00, 11: 18.00, 12: 22.00,
                13: 189.00, 14: 245.00, 15: 380.00, 16: 135.00, 17: 142.00, 18: 98.00,
                19: 49.90, 20: 21.00, 21: 87.00, 22: 215.00, 23: 27.50, 24: 18.50,
                25: 54.90, 26: 23.00, 27: 119.00, 28: 46.00, 29: 38.00, 30: 62.00,
                31: 45.00, 32: 39.90, 33: 58.00, 34: 89.00, 35: 52.00,
                36: 19.90, 37: 17.50, 38: 16.00, 39: 72.00, 40: 65.00,
                41: 89.00, 42: 320.00, 43: 215.00, 44: 175.00, 45: 132.00,
                46: 42.00, 47: 34.00, 48: 36.00, 49: 165.00, 50: 28.00,
            }

            # 3. Store Products (80)
            store_products = []
            upc_list = []
            for i in range(1, 61):
                upc = f"{i:012d}"
                upc_list.append(upc)
                pid = i if i <= 50 else random.randint(1, 49)
                price = product_prices[pid]
                # 20% chance of 0 stock for Out-Of-Stock testing
                qty = random.choice([0, 0, 10, 50, 100, 200])
                store_products.append(
                    (
                        upc,
                        None,
                        pid,
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
            # (surname, name, patronymic, city, street) — realistic Ukrainian names.
            employee_people = [
                ("Шевченко", "Андрій", "Миколайович", "Київ", "вул. Хрещатик, 12"),
                ("Коваленко", "Олена", "Петрівна", "Київ", "вул. Володимирська, 45"),
                ("Бондаренко", "Ірина", "Василівна", "Київ", "вул. Саксаганського, 8"),
                ("Ткаченко", "Сергій", "Олегович", "Київ", "вул. Антоновича, 23"),
                ("Мельник", "Наталія", "Іванівна", "Київ", "вул. Гончара, 17"),
                ("Кравчук", "Дмитро", "Анатолійович", "Київ", "просп. Перемоги, 56"),
                ("Поліщук", "Тетяна", "Степанівна", "Київ", "вул. Лесі Українки, 9"),
                ("Савченко", "Олександр", "Юрійович", "Київ", "вул. Дегтярівська, 31"),
                ("Гриценко", "Марія", "Богданівна", "Київ", "вул. Січових Стрільців, 4"),
                ("Лисенко", "Віктор", "Романович", "Київ", "вул. Велика Васильківська, 72"),
            ]
            employees = []
            roles = ["Manager", "Manager"] + ["Cashier"] * 8
            cashier_ids = []
            for i in range(1, 11):
                emp_id = f"EMP{i:02d}"
                if roles[i - 1] == "Cashier":
                    cashier_ids.append(emp_id)
                surname, name, patronymic, city, street = employee_people[i - 1]
                employees.append(
                    (
                        emp_id,
                        surname,
                        name,
                        patronymic,
                        roles[i - 1],
                        15000.0 + random.randint(0, 5000),
                        "1995-01-01",
                        "2023-01-01",
                        f"+38099{i:07d}",
                        city,
                        street,
                        f"010{i:02d}",
                        make_password(emp_id),
                    )
                )
            cursor.executemany(
                """
                               INSERT INTO employee (id_employee, empl_surname, empl_name, empl_patronymic, empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code, password_hash)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               """,
                employees,
            )

            # 5. Customer Cards (30) — realistic Ukrainian names; some without address.
            cust_surnames = [
                "Іваненко", "Петренко", "Сидоренко", "Коваль", "Бойко",
                "Ткач", "Марченко", "Руденко", "Захарченко", "Романюк",
                "Гончар", "Кравець", "Мороз", "Левченко", "Павленко",
            ]
            cust_names = [
                "Олег", "Ірина", "Андрій", "Оксана", "Михайло",
                "Світлана", "Юрій", "Галина", "Ігор", "Людмила",
                "Тарас", "Наталя", "Богдан", "Вікторія", "Роман",
            ]
            cust_cities = ["Львів", "Харків", "Одеса", "Дніпро", "Полтава"]
            cards = []
            card_ids = []
            for i in range(1, 31):
                card_id = f"CARD{i:09d}"
                card_ids.append(card_id)
                pct = random.choice([0, 5, 10, 15, 20])
                has_address = random.choice([True, False])
                surname = cust_surnames[(i - 1) % len(cust_surnames)]
                name = cust_names[((i - 1) * 7) % len(cust_names)]
                city = cust_cities[(i - 1) % len(cust_cities)] if has_address else None
                cards.append(
                    (
                        card_id,
                        surname,
                        name,
                        f"+38050{i:07d}",
                        city,
                        f"вул. Личаківська, {i}" if has_address else None,
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
                           UPDATE "check" c
                           SET sum_total = COALESCE(
                                   (SELECT SUM(product_number * selling_price) FROM sale s WHERE s.check_number = c.check_number)
                                       * (1 - COALESCE((SELECT percent FROM customer_card cc WHERE cc.card_number = c.card_number), 0) / 100.0),
                                   0);

                           UPDATE "check"
                           SET vat = sum_total * 0.2;
                           """)

        self.stdout.write(
            self.style.SUCCESS(
                f"Success! Generated 10 categories, 50 products, 80 store products, 10 employees, 30 cards, 500 checks, and {len(sales)} sales."
            )
        )
