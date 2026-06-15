import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from . import queries

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ==========================================


def validate_sort_column(sort_column, allowed_columns):
    """Перевірка колонки для сортування (захист від SQL-ін'єкцій)."""
    if not sort_column or sort_column not in allowed_columns:
        return allowed_columns[0]  # Значення за замовчуванням
    return sort_column


# Білі списки колонок для кожної таблиці
EMP_SORT_COLS = ["empl_surname", "empl_name", "empl_role", "salary", "date_of_start"]
CARD_SORT_COLS = ["cust_surname", "percent", "city"]
STORE_PROD_SORT_COLS = ["products_number", "selling_price", '"UPC"']

# ==========================================
# 1. CATEGORY VIEWS (Категорії)
# ==========================================


@csrf_exempt
@require_http_methods(["GET", "POST"])
def category_list_create(request):
    if request.method == "GET":
        categories = queries.get_all_categories()
        return JsonResponse({"results": categories}, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            queries.add_category(data["category_number"], data["category_name"])
            return JsonResponse({"message": "Категорію успішно створено"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def category_detail(request, category_number):
    if request.method == "GET":
        category = queries.fetch_one(
            "SELECT * FROM category WHERE category_number = %s", [category_number]
        )
        if not category:
            return JsonResponse({"error": "Категорію не знайдено"}, status=404)
        return JsonResponse(category)

    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            queries.execute(
                "UPDATE category SET category_name = %s WHERE category_number = %s",
                [data.get("category_name"), category_number],
            )
            return JsonResponse({"message": "Категорію оновлено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            queries.delete_category(category_number)
            return JsonResponse({"message": "Категорію видалено"})
        except IntegrityError:
            return JsonResponse(
                {"error": "Cannot delete: products are attached to this category."},
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 2. EMPLOYEE VIEWS (Працівники)
# ==========================================


@csrf_exempt
@require_http_methods(["GET", "POST"])
def employee_list_create(request):
    if request.method == "GET":
        role = request.GET.get("role")
        sort = validate_sort_column(request.GET.get("sort"), EMP_SORT_COLS)

        query = "SELECT * FROM employee WHERE 1=1"
        params = []

        if role:
            query += " AND empl_role = %s"
            params.append(role)

        query += f" ORDER BY {sort}"
        employees = queries.fetch_all(query, params)

        return JsonResponse({"results": employees}, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            queries.execute(
                """INSERT INTO employee (id_employee, empl_surname, empl_name, empl_patronymic,
                                         empl_role, salary, date_of_birth, date_of_start, phone_number, city, street, zip_code)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [
                    data["id_employee"],
                    data["empl_surname"],
                    data["empl_name"],
                    data.get("empl_patronymic"),
                    data["empl_role"],
                    data["salary"],
                    data["date_of_birth"],
                    data["date_of_start"],
                    data["phone_number"],
                    data["city"],
                    data["street"],
                    data["zip_code"],
                ],
            )
            return JsonResponse({"message": "Працівника створено"}, status=201)
        except IntegrityError:
            return JsonResponse(
                {"error": "Constraint violation. Check age (>=18) or phone format."},
                status=400,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def employee_detail(request, id_employee):
    if request.method == "GET":
        employee = queries.fetch_one(
            "SELECT * FROM employee WHERE id_employee = %s", [id_employee]
        )
        if not employee:
            return JsonResponse({"error": "Працівника не знайдено"}, status=404)
        return JsonResponse(employee)

    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            queries.execute(
                """UPDATE employee SET empl_surname = %s, empl_name = %s, empl_patronymic = %s,
                                       empl_role = %s, salary = %s, date_of_birth = %s, date_of_start = %s,
                                       phone_number = %s, city = %s, street = %s, zip_code = %s
                   WHERE id_employee = %s""",
                [
                    data.get("empl_surname"),
                    data.get("empl_name"),
                    data.get("empl_patronymic"),
                    data.get("empl_role"),
                    data.get("salary"),
                    data.get("date_of_birth"),
                    data.get("date_of_start"),
                    data.get("phone_number"),
                    data.get("city"),
                    data.get("street"),
                    data.get("zip_code"),
                    id_employee,
                ],
            )
            return JsonResponse({"message": "Дані працівника оновлено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            queries.execute(
                "DELETE FROM employee WHERE id_employee = %s", [id_employee]
            )
            return JsonResponse({"message": "Працівника видалено"})
        except IntegrityError:
            return JsonResponse(
                {"error": "Неможливо видалити касира, який вже створював чеки."},
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 3. CUSTOMER CARD VIEWS (Карти клієнтів)
# ==========================================


@csrf_exempt
@require_http_methods(["GET", "POST"])
def customer_card_list_create(request):
    if request.method == "GET":
        percent = request.GET.get("percent")
        sort = validate_sort_column(request.GET.get("sort"), CARD_SORT_COLS)

        query = "SELECT * FROM customer_card WHERE 1=1"
        params = []

        if percent:
            query += " AND percent = %s"
            params.append(percent)

        query += f" ORDER BY {sort}"
        cards = queries.fetch_all(query, params)

        return JsonResponse({"results": cards}, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            queries.execute(
                """INSERT INTO customer_card (card_number, cust_surname, cust_name, cust_patronymic,
                                              phone_number, city, street, zip_code, percent)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [
                    data["card_number"],
                    data["cust_surname"],
                    data["cust_name"],
                    data.get("cust_patronymic"),
                    data["phone_number"],
                    data.get("city"),
                    data.get("street"),
                    data.get("zip_code"),
                    data["percent"],
                ],
            )
            return JsonResponse({"message": "Картку клієнта створено"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def customer_card_detail(request, card_number):
    if request.method == "GET":
        card = queries.get_customer_card_by_number(card_number)
        if not card:
            return JsonResponse({"error": "Картку не знайдено"}, status=404)
        return JsonResponse(card)

    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            queries.execute(
                """UPDATE customer_card SET cust_surname = %s, cust_name = %s, cust_patronymic = %s,
                                            phone_number = %s, city = %s, street = %s, zip_code = %s, percent = %s
                   WHERE card_number = %s""",
                [
                    data.get("cust_surname"),
                    data.get("cust_name"),
                    data.get("cust_patronymic"),
                    data.get("phone_number"),
                    data.get("city"),
                    data.get("street"),
                    data.get("zip_code"),
                    data.get("percent"),
                    card_number,
                ],
            )
            return JsonResponse({"message": "Картку клієнта оновлено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            queries.execute(
                "DELETE FROM customer_card WHERE card_number = %s", [card_number]
            )
            return JsonResponse({"message": "Картку клієнта видалено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 4. PRODUCT VIEWS (Товари у довіднику)
# ==========================================


@csrf_exempt
@require_http_methods(["GET", "POST"])
def product_list_create(request):
    if request.method == "GET":
        category = request.GET.get("category")
        search = request.GET.get("search")

        query = """SELECT p.*, c.category_name FROM product p
                                                        JOIN category c ON p.category_number = c.category_number WHERE 1=1"""
        params = []

        if category:
            query += " AND p.category_number = %s"
            params.append(category)
        if search:
            query += " AND p.product_name ILIKE %s"
            params.append(f"%{search}%")

        query += " ORDER BY p.product_name"
        products = queries.fetch_all(query, params)
        return JsonResponse({"results": products}, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            queries.execute(
                """INSERT INTO product (id_product, category_number, product_name, characteristics)
                   VALUES (%s, %s, %s, %s)""",
                [
                    data["id_product"],
                    data["category_number"],
                    data["product_name"],
                    data["characteristics"],
                ],
            )
            return JsonResponse({"message": "Товар створено"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def product_detail(request, id_product):
    if request.method == "GET":
        product = queries.fetch_one(
            """SELECT p.*, c.category_name FROM product p
                                                    JOIN category c ON p.category_number = c.category_number WHERE p.id_product = %s""",
            [id_product],
        )
        if not product:
            return JsonResponse({"error": "Товар не знайдено"}, status=404)
        return JsonResponse(product)

    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            queries.execute(
                """UPDATE product SET category_number = %s, product_name = %s, characteristics = %s
                   WHERE id_product = %s""",
                [
                    data.get("category_number"),
                    data.get("product_name"),
                    data.get("characteristics"),
                    id_product,
                ],
            )
            return JsonResponse({"message": "Товар оновлено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            queries.execute("DELETE FROM product WHERE id_product = %s", [id_product])
            return JsonResponse({"message": "Товар видалено"})
        except IntegrityError:
            return JsonResponse(
                {
                    "error": "Неможливо видалити: товар уже є на вітрині (store_product)."
                },
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 5. STORE PRODUCT VIEWS (Товари на вітрині)
# ==========================================


@csrf_exempt
@require_http_methods(["GET", "POST"])
def store_product_list_create(request):
    if request.method == "GET":
        promotional = request.GET.get("promotional")
        sort = validate_sort_column(request.GET.get("sort"), STORE_PROD_SORT_COLS)

        query = """SELECT sp.*, p.product_name, c.category_name
                   FROM store_product sp
                            JOIN product p ON sp.id_product = p.id_product
                            JOIN category c ON p.category_number = c.category_number
                   WHERE 1=1"""
        params = []

        if promotional == "true":
            query += " AND sp.promotional_product = TRUE"
        elif promotional == "false":
            query += " AND sp.promotional_product = FALSE"

        query += f" ORDER BY {sort}"
        products = queries.fetch_all(query, params)

        return JsonResponse({"results": products}, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            queries.execute(
                """INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                [
                    data["UPC"],
                    data.get("UPC_prom"),
                    data["id_product"],
                    data["selling_price"],
                    data["products_number"],
                    data["promotional_product"],
                ],
            )
            return JsonResponse({"message": "Товар додано до магазину"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def store_product_detail(request, upc):
    if request.method == "GET":
        product = queries.fetch_one(
            """SELECT sp.*, p.product_name FROM store_product sp
                                                    JOIN product p ON sp.id_product = p.id_product WHERE sp."UPC" = %s""",
            [upc],
        )
        if not product:
            return JsonResponse({"error": "Товар не знайдено"}, status=404)
        return JsonResponse(product)

    elif request.method == "PUT":
        data = json.loads(request.body)
        try:
            queries.execute(
                """UPDATE store_product SET "UPC_prom" = %s, id_product = %s, selling_price = %s,
                                            products_number = %s, promotional_product = %s WHERE "UPC" = %s""",
                [
                    data.get("UPC_prom"),
                    data.get("id_product"),
                    data.get("selling_price"),
                    data.get("products_number"),
                    data.get("promotional_product"),
                    upc,
                ],
            )
            return JsonResponse({"message": "Дані товару в магазині оновлено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            queries.execute('DELETE FROM store_product WHERE "UPC" = %s', [upc])
            return JsonResponse({"message": "Товар видалено з магазину"})
        except IntegrityError:
            return JsonResponse(
                {"error": "Cannot delete: product is already included in checks."},
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 6. CHECK VIEWS (Чеки та Продажі) - ТРАНЗАКЦІЯ
# ==========================================


@csrf_exempt
@require_http_methods(["GET", "POST"])
def check_list_create(request):
    if request.method == "GET":
        id_employee = request.GET.get("id_employee")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        query = """SELECT c.*, e.empl_surname, e.empl_name FROM "check" c
                                                                    JOIN employee e ON c.id_employee = e.id_employee WHERE 1=1"""
        params = []

        if id_employee:
            query += " AND c.id_employee = %s"
            params.append(id_employee)
        if date_from:
            query += " AND c.print_date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND c.print_date <= %s"
            params.append(date_to)

        query += " ORDER BY c.print_date DESC"
        checks = queries.fetch_all(query, params)

        return JsonResponse({"results": checks}, safe=False)

    elif request.method == "POST":
        data = json.loads(request.body)

        check_number = data.get("check_number")
        id_employee = data.get("id_employee")
        card_number = data.get("card_number")
        print_date = data.get("print_date", datetime.now())
        products = data.get("products", [])

        if not products:
            return JsonResponse({"error": "Чек не може бути порожнім"}, status=400)

        try:
            with transaction.atomic():
                sum_total = 0
                processed_products = []

                # 1. Збираємо АКТУАЛЬНІ ціни та рахуємо загальну суму ДО створення чека
                for product in products:
                    actual_product = queries.fetch_one(
                        'SELECT selling_price FROM store_product WHERE "UPC" = %s FOR UPDATE',
                        [product["UPC"]],
                    )
                    if not actual_product:
                        raise Exception(f"Товар з UPC {product['UPC']} не знайдено.")

                    real_price = float(actual_product["selling_price"])
                    qty = float(product["product_number"])
                    sum_total += qty * real_price

                    # Зберігаємо реальні дані для наступного кроку
                    processed_products.append(
                        {
                            "UPC": product["UPC"],
                            "product_number": product["product_number"],
                            "selling_price": real_price,
                        }
                    )

                vat = sum_total * 0.2

                # 2. Створюємо шапку чека (тепер маємо валідні sum_total та vat)
                queries.execute(
                    """
                    INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [
                        check_number,
                        id_employee,
                        card_number,
                        print_date,
                        sum_total,
                        vat,
                    ],
                )

                # 3. Записуємо кожен товар у Sale і віднімаємо кількість зі складу
                for pp in processed_products:
                    queries.execute(
                        """
                        INSERT INTO sale ("UPC", check_number, product_number, selling_price)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [
                            pp["UPC"],
                            check_number,
                            pp["product_number"],
                            pp["selling_price"],
                        ],
                    )

                    queries.execute(
                        """
                        UPDATE store_product
                        SET products_number = products_number - %s
                        WHERE "UPC" = %s
                        """,
                        [pp["product_number"], pp["UPC"]],
                    )

            return JsonResponse(
                {"message": "Чек успішно створено", "check_number": check_number},
                status=201,
            )

        except IntegrityError:
            return JsonResponse(
                {"error": "Недостатньо товару на складі або невірні дані чека."},
                status=400,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def check_detail(request, check_number):
    if request.method == "GET":
        check = queries.fetch_one(
            """SELECT c.*, e.empl_surname, e.empl_name FROM "check" c
                                                                JOIN employee e ON c.id_employee = e.id_employee WHERE c.check_number = %s""",
            [check_number],
        )
        if not check:
            return JsonResponse({"error": "Чек не знайдено"}, status=404)

        items = queries.fetch_all(
            """SELECT s.product_number, s.selling_price, p.product_name
               FROM sale s
                        JOIN store_product sp ON s."UPC" = sp."UPC"
                        JOIN product p ON sp.id_product = p.id_product
               WHERE s.check_number = %s""",
            [check_number],
        )
        return JsonResponse({"check": check, "items": items})

    elif request.method == "DELETE":
        try:
            queries.execute(
                'DELETE FROM "check" WHERE check_number = %s', [check_number]
            )
            return JsonResponse({"message": "Чек видалено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 7. REPORT VIEWS (Звіти)
# ==========================================


@require_http_methods(["GET"])
def report_sales_revenue(request):
    id_employee = request.GET.get("id_employee")
    start = request.GET.get("start")
    end = request.GET.get("end")

    query = 'SELECT SUM(sum_total) as total_revenue FROM "check" WHERE 1=1'
    params = []

    if id_employee:
        query += " AND id_employee = %s"
        params.append(id_employee)
    if start:
        query += " AND print_date >= %s"
        params.append(start)
    if end:
        query += " AND print_date <= %s"
        params.append(end)

    result = queries.fetch_one(query, params)
    return JsonResponse(
        {
            "total_revenue": (
                result["total_revenue"] if result and result["total_revenue"] else 0
            )
        }
    )


@require_http_methods(["GET"])
def report_product_volume(request):
    upc = request.GET.get("upc")
    start = request.GET.get("start")
    end = request.GET.get("end")

    query = """SELECT SUM(s.product_number) as total_volume FROM sale s
                                                                     JOIN "check" c ON s.check_number = c.check_number WHERE 1=1"""
    params = []

    if upc:
        query += ' AND s."UPC" = %s'
        params.append(upc)
    if start:
        query += " AND c.print_date >= %s"
        params.append(start)
    if end:
        query += " AND c.print_date <= %s"
        params.append(end)

    result = queries.fetch_one(query, params)
    return JsonResponse(
        {
            "total_volume": (
                result["total_volume"] if result and result["total_volume"] else 0
            )
        }
    )


@require_http_methods(["GET"])
def report_total_sold_per_product(request):
    return JsonResponse({"results": queries.get_total_sold_per_product()}, safe=False)


@require_http_methods(["GET"])
def report_customers_served_by_all_cashiers(request):
    return JsonResponse(
        {"results": queries.get_customers_served_by_all_cashiers()}, safe=False
    )


@require_http_methods(["GET"])
def report_top_cashiers(request):
    start = request.GET.get("start", "1970-01-01")
    end = request.GET.get("end", "2100-01-01")
    return JsonResponse(
        {"results": queries.get_top_cashiers_for_period(start, end)}, safe=False
    )


@require_http_methods(["GET"])
def report_categories_all_products_sold(request):
    return JsonResponse(
        {"results": queries.get_categories_with_all_products_sold()}, safe=False
    )


@require_http_methods(["GET"])
def report_total_sold_per_category(request):
    return JsonResponse({"results": queries.get_total_sold_per_category()}, safe=False)


@require_http_methods(["GET"])
def report_employees_served_all_customers(request):
    return JsonResponse(
        {"results": queries.get_employees_who_served_all_card_customers()}, safe=False
    )


# ==========================================
# 8. UI DROPDOWNS VIEW (Для дружнього інтерфейсу)
# ==========================================


@require_http_methods(["GET"])
def ui_dropdowns(request, entity):
    entity_map = {
        "categories": "SELECT category_number as id, category_name as name FROM category ORDER BY category_name",
        "employees": "SELECT id_employee as id, CONCAT(empl_surname, ' ', empl_name) as name FROM employee ORDER BY empl_surname",
        "products": "SELECT id_product as id, product_name as name FROM product ORDER BY product_name",
        "customer-cards": "SELECT card_number as id, CONCAT(cust_surname, ' ', cust_name) as name FROM customer_card ORDER BY cust_surname",
    }

    query = entity_map.get(entity)
    if not query:
        return JsonResponse({"error": "Невідома сутність"}, status=400)

    results = queries.fetch_all(query)
    return JsonResponse({"results": results}, safe=False)
