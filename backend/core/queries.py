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
