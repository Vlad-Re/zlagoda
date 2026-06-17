from django.db import connection


def dictfetchall(cursor):
    """Convert SQL query result from list of tuples to list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor):
    """Convert a single result row to a dictionary."""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(zip(columns, row))


def execute(query, params=None):
    """For INSERT, UPDATE, DELETE queries (which do not return results)."""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])


def fetch_all(query, params=None):
    """For SELECT queries that return multiple rows."""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return dictfetchall(cursor)


def fetch_one(query, params=None):
    """For SELECT queries that search for a specific record (e.g., by ID)."""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return dictfetchone(cursor)


def get_all_categories():
    return fetch_all("SELECT * FROM category ORDER BY category_name;")


def add_category(category_number, category_name):
    execute(
        "INSERT INTO category (category_number, category_name) VALUES (%s, %s)",
        [category_number, category_name],
    )


def delete_category(category_number):
    execute("DELETE FROM category WHERE category_number = %s", [category_number])


def get_all_customer_cards():
    return fetch_all("SELECT * FROM customer_card ORDER BY cust_surname, cust_name;")


def get_customer_card_by_number(card_number):
    return fetch_one(
        "SELECT * FROM customer_card WHERE card_number = %s", [card_number]
    )


def get_all_employees():
    return fetch_all("SELECT * FROM employee ORDER BY empl_surname, empl_name;")


def get_cashiers():
    return fetch_all(
        "SELECT * FROM employee WHERE empl_role = 'Cashier' ORDER BY empl_surname;"
    )


def get_all_products_with_categories():
    query = """
            SELECT p.id_product, p.product_name, p.characteristics, c.category_name
            FROM product p
                     JOIN category c ON p.category_number = c.category_number
            ORDER BY p.product_name; \
            """
    return fetch_all(query)


def apply_expiry_promotions():
    """Business rule: a store product automatically goes on sale when it is
    close to expiring (within 3 days) and there is plenty of stock left
    (more than 10 units). The flag is only switched on — products that were
    set promotional by other means are left untouched."""
    execute(
        """
        UPDATE store_product
        SET promotional_product = TRUE
        WHERE promotional_product = FALSE
          AND expire_date IS NOT NULL
          AND expire_date >= CURRENT_DATE
          AND expire_date <= CURRENT_DATE + INTERVAL '3 days'
          AND products_number > 10
        """
    )


def get_promotional_products():
    query = """
            SELECT sp."UPC", sp.selling_price, sp.products_number, p.product_name
            FROM store_product sp
                     JOIN product p ON sp.id_product = p.id_product
            WHERE sp.promotional_product = TRUE
            ORDER BY p.product_name; \
            """
    return fetch_all(query)


def get_total_sales_in_period(start_date, end_date):
    query = """
            SELECT SUM(sum_total) as total_revenue
            FROM "check"
            WHERE print_date >= %s AND print_date <= %s; \
            """
    result = fetch_one(query, [start_date, end_date])
    return result["total_revenue"] if result else 0


def get_check_details(check_number):
    query = """
            SELECT s.product_number, s.selling_price, p.product_name
            FROM sale s
                     JOIN store_product sp ON s."UPC" = sp."UPC"
                     JOIN product p ON sp.id_product = p.id_product
            WHERE s.check_number = %s; \
            """
    return fetch_all(query, [check_number])


# ==========================================
# ДОДАТКОВІ СКЛАДНІ ЗАПИТИ (Advanced Options)
# ==========================================


def get_total_sold_per_product():
    """Знайти загальну кількість проданих одиниць для кожного найменування товару."""
    query = """
            SELECT p.product_name, SUM(s.product_number) AS total_sold
            FROM product p
                     INNER JOIN store_product sp ON p.id_product = sp.id_product
                     INNER JOIN sale s ON sp."UPC" = s."UPC"
            GROUP BY p.product_name
            ORDER BY total_sold DESC;
            """
    return fetch_all(query)


def get_customers_served_by_all_cashiers():
    """Знайти постійних клієнтів, яких обслуговували абсолютно всі касири (Реляційне ділення)."""
    query = """
            SELECT c.cust_surname, c.cust_name
            FROM customer_card c
            WHERE NOT EXISTS (
                SELECT e.id_employee
                FROM employee e
                WHERE e.empl_role = 'Cashier'
                  AND NOT EXISTS (
                    SELECT ch.check_number
                    FROM "check" ch
                    WHERE ch.card_number = c.card_number
                      AND ch.id_employee = e.id_employee
                )
            ); \
            """
    return fetch_all(query)


def get_top_cashiers_for_period(start_date, end_date):
    """
    Визначити найприбутковіших касирів за період.
    Повертає лише тих, хто має більше 5 чеків. Сортування за виручкою.
    """
    query = """
            SELECT e.id_employee, e.empl_surname, e.empl_name,
                   COUNT(DISTINCT ch.check_number) AS checks_count,
                   SUM(s.product_number * s.selling_price) AS revenue,
                   ROUND(SUM(s.product_number * s.selling_price) / COUNT(DISTINCT ch.check_number), 2) AS avg_check
            FROM employee e
                     INNER JOIN "check" ch ON e.id_employee = ch.id_employee
                     INNER JOIN sale s ON ch.check_number = s.check_number
            WHERE ch.print_date >= %s AND ch.print_date <= %s
            GROUP BY e.id_employee, e.empl_surname, e.empl_name
            HAVING COUNT(DISTINCT ch.check_number) > 5
            ORDER BY revenue DESC;
            """
    return fetch_all(query, [start_date, end_date])


def get_categories_with_all_products_sold():
    """Знайти категорії товарів, кожен з товарів якої був проданий хоча б один раз."""
    query = """
            SELECT c.category_number, c.category_name
            FROM category c
            WHERE NOT EXISTS (
                SELECT 1
                FROM product p
                WHERE p.category_number = c.category_number
                  AND NOT EXISTS (
                    SELECT 1
                    FROM store_product sp
                             INNER JOIN sale s ON sp."UPC" = s."UPC"
                    WHERE sp.id_product = p.id_product
                )
            ); \
            """
    return fetch_all(query)

# VladR query
def get_total_sold_per_category(start_date, end_date):
    """Знайти загальну кількість проданих одиниць товарів для кожної категорії продукції за вказаний період часу."""
    query = """
            SELECT c.category_name, SUM(s.product_number) AS total_sold
            FROM category c
                     INNER JOIN product p ON c.category_number = p.category_number
                     INNER JOIN store_product sp ON p.id_product = sp.id_product
                     INNER JOIN sale s ON sp."UPC" = s."UPC"
                     INNER JOIN "check" ch ON s.check_number = ch.check_number
            WHERE ch.print_date >= %s AND ch.print_date <= %s
            GROUP BY c.category_name
            ORDER BY total_sold DESC;
            """
    return fetch_all(query, [start_date, end_date])

# VladR query
def get_employees_who_served_all_card_customers():
    """Знайти працівників, які пробили хоча б один чек абсолютно кожному існуючому клієнту з карткою лояльності."""
    query = """
            SELECT e.empl_surname, e.empl_name
            FROM employee e
            WHERE NOT EXISTS (
                SELECT 1
                FROM customer_card c
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM "check" ch
                    WHERE ch.id_employee = e.id_employee
                      AND ch.card_number = c.card_number
                )
            );
            """
    return fetch_all(query)


# ==========================================
# AUTH QUERIES
# ==========================================

EMPLOYEE_SAFE_COLS = (
    "id_employee, empl_surname, empl_name, empl_patronymic, empl_role, "
    "salary, date_of_birth, date_of_start, phone_number, city, street, zip_code"
)


def get_employee_for_auth(id_employee):
    return fetch_one(
        "SELECT id_employee, empl_role, empl_surname, empl_name, password_hash "
        "FROM employee WHERE id_employee = %s",
        [id_employee],
    )


def get_employee_profile(id_employee):
    return fetch_one(
        f"SELECT {EMPLOYEE_SAFE_COLS} FROM employee WHERE id_employee = %s",
        [id_employee],
    )
