import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from django.contrib.auth.hashers import make_password, check_password
from . import queries
from .decorators import login_required_api, manager_required

# ==========================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ==========================================

EMPLOYEE_SAFE_COLS = (
    "id_employee, empl_surname, empl_name, empl_patronymic, empl_role, "
    "salary, date_of_birth, date_of_start, phone_number, city, street, zip_code"
)


def validate_sort_column(sort_column, allowed_columns):
    if not sort_column or sort_column not in allowed_columns:
        return allowed_columns[0]
    return sort_column


# Products that go on sale because they are about to expire are sold at this
# discount off their listed price (20% off => customer pays 80%).
EXPIRY_SALE_DISCOUNT = 0.20

# SQL boolean that is TRUE when a store_product currently qualifies for the
# expiry sale (close to expiry + plenty of stock). Mirrors apply_expiry_promotions.
ON_SALE_SQL = (
    "(expire_date IS NOT NULL "
    "AND expire_date >= CURRENT_DATE "
    "AND expire_date <= CURRENT_DATE + INTERVAL '3 days' "
    "AND products_number > 10)"
)

EMP_SORT_COLS = ["empl_surname", "empl_name", "empl_role", "salary", "date_of_start"]
CARD_SORT_COLS = ["card_number", "cust_surname", "cust_name", "percent", "city"]
STORE_PROD_SORT_COLS = [
    "products_number",
    "selling_price",
    '"UPC"',
    "p.product_name",
    "c.category_name",
    "expire_date",
    "promotional_product",
]


# ==========================================
# AUTH VIEWS
# ==========================================


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    data = json.loads(request.body)
    id_employee = data.get("id_employee", "").strip()
    password = data.get("password", "")

    if not id_employee or not password:
        return JsonResponse({"error": "ID та пароль є обов'язковими"}, status=400)

    employee = queries.get_employee_for_auth(id_employee)
    if not employee or not check_password(password, employee["password_hash"]):
        return JsonResponse({"error": "Невірний ID або пароль"}, status=401)

    request.session["employee_id"] = employee["id_employee"]
    request.session["role"] = employee["empl_role"]

    return JsonResponse(
        {
            "id_employee": employee["id_employee"],
            "role": employee["empl_role"],
            "name": f"{employee['empl_surname']} {employee['empl_name']}",
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@login_required_api
def logout_view(request):
    request.session.flush()
    return JsonResponse({"message": "Вихід виконано"})


@require_http_methods(["GET"])
@login_required_api
def me_view(request):
    employee = queries.get_employee_profile(request.session["employee_id"])
    if not employee:
        request.session.flush()
        return JsonResponse({"error": "Сесію анульовано"}, status=401)
    employee["role"] = request.session["role"]
    return JsonResponse(employee)


# ==========================================
# 1. CATEGORY VIEWS
# ==========================================


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "POST"])
def category_list_create(request):
    if request.method == "GET":
        categories = queries.get_all_categories()
        return JsonResponse({"results": categories}, safe=False)

    # POST — manager only
    if request.session.get("role") != "Manager":
        return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)

    data = json.loads(request.body)
    try:
        queries.add_category(data["category_number"], data["category_name"])
        return JsonResponse({"message": "Категорію успішно створено"}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "PUT", "DELETE"])
def category_detail(request, category_number):
    if request.method == "GET":
        category = queries.fetch_one(
            "SELECT * FROM category WHERE category_number = %s", [category_number]
        )
        if not category:
            return JsonResponse({"error": "Категорію не знайдено"}, status=404)
        return JsonResponse(category)

    if request.session.get("role") != "Manager":
        return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)

    if request.method == "PUT":
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
                {"error": "Неможливо видалити: до категорії прив'язані товари."},
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 2. EMPLOYEE VIEWS
# ==========================================


@csrf_exempt
@manager_required
@require_http_methods(["GET", "POST"])
def employee_list_create(request):
    if request.method == "GET":
        role = request.GET.get("role")
        sort = validate_sort_column(request.GET.get("sort"), EMP_SORT_COLS)
        surname = request.GET.get("surname")

        query = f"SELECT {EMPLOYEE_SAFE_COLS} FROM employee WHERE 1=1"
        params = []

        if role:
            query += " AND empl_role = %s"
            params.append(role)
        if surname:
            query += " AND empl_surname ILIKE %s"
            params.append(f"%{surname}%")

        query += f" ORDER BY {sort}"
        employees = queries.fetch_all(query, params)
        return JsonResponse({"results": employees}, safe=False)

    data = json.loads(request.body)

    date_error = validate_employee_dates(
        data.get("date_of_birth"), data.get("date_of_start")
    )
    if date_error:
        return JsonResponse({"error": date_error}, status=400)

    raw_password = data.get("password") or data["id_employee"]
    try:
        queries.execute(
            f"""INSERT INTO employee
                (id_employee, empl_surname, empl_name, empl_patronymic, empl_role,
                 salary, date_of_birth, date_of_start, phone_number, city, street,
                 zip_code, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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
                make_password(raw_password),
            ],
        )
        return JsonResponse({"message": "Працівника створено"}, status=201)
    except IntegrityError:
        return JsonResponse(
            {"error": "Порушення обмежень. Перевірте вік (>=18) або формат телефону."},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@manager_required
@require_http_methods(["GET", "PUT", "DELETE"])
def employee_detail(request, id_employee):
    if request.method == "GET":
        employee = queries.fetch_one(
            f"SELECT {EMPLOYEE_SAFE_COLS} FROM employee WHERE id_employee = %s",
            [id_employee],
        )
        if not employee:
            return JsonResponse({"error": "Працівника не знайдено"}, status=404)
        return JsonResponse(employee)

    elif request.method == "PUT":
        data = json.loads(request.body)

        date_error = validate_employee_dates(
            data.get("date_of_birth"), data.get("date_of_start")
        )
        if date_error:
            return JsonResponse({"error": date_error}, status=400)

        try:
            extra_set = ""
            extra_params = []
            if data.get("password"):
                extra_set = ", password_hash = %s"
                extra_params = [make_password(data["password"])]

            queries.execute(
                f"""UPDATE employee
                    SET empl_surname = %s, empl_name = %s, empl_patronymic = %s,
                        empl_role = %s, salary = %s, date_of_birth = %s, date_of_start = %s,
                        phone_number = %s, city = %s, street = %s, zip_code = %s{extra_set}
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
                    *extra_params,
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


@require_http_methods(["GET"])
@manager_required
def employee_search(request):
    surname = request.GET.get("surname", "")
    employees = queries.fetch_all(
        "SELECT empl_surname, empl_name, phone_number, city, street, zip_code "
        "FROM employee WHERE empl_surname ILIKE %s ORDER BY empl_surname",
        [f"%{surname}%"],
    )
    return JsonResponse({"results": employees})


# ==========================================
# 3. CUSTOMER CARD VIEWS
# ==========================================


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "POST"])
def customer_card_list_create(request):
    if request.method == "GET":
        percent = request.GET.get("percent")
        sort = validate_sort_column(request.GET.get("sort"), CARD_SORT_COLS)
        direction = "DESC" if request.GET.get("dir") == "desc" else "ASC"
        surname = request.GET.get("surname")

        query = "SELECT * FROM customer_card WHERE 1=1"
        params = []

        if percent:
            query += " AND percent = %s"
            params.append(percent)
        if surname:
            query += " AND cust_surname ILIKE %s"
            params.append(f"%{surname}%")

        query += f" ORDER BY {sort} {direction}"
        cards = queries.fetch_all(query, params)
        return JsonResponse({"results": cards}, safe=False)

    data = json.loads(request.body)

    percent = data.get("percent")
    if percent is not None:
        try:
            percent_val = int(percent)
            if percent_val < 0 or percent_val > 100:
                return JsonResponse(
                    {"error": "Відсоток знижки має бути від 0 до 100."}, status=400
                )
        except ValueError:
            return JsonResponse(
                {"error": "Відсоток знижки має бути числом."}, status=400
            )

    try:
        queries.execute(
            """INSERT INTO customer_card
               (card_number, cust_surname, cust_name, cust_patronymic,
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
    except IntegrityError:
        return JsonResponse(
            {
                "error": "Помилка збереження. Перевірте унікальність номера картки або інші обмеження."
            },
            status=400,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "PUT", "DELETE"])
def customer_card_detail(request, card_number):
    if request.method == "GET":
        card = queries.get_customer_card_by_number(card_number)
        if not card:
            return JsonResponse({"error": "Картку не знайдено"}, status=404)
        return JsonResponse(card)

    elif request.method == "PUT":
        data = json.loads(request.body)
        percent = data.get("percent")
        if percent is not None:
            try:
                percent_val = int(percent)
                if percent_val < 0 or percent_val > 100:
                    return JsonResponse(
                        {"error": "Відсоток знижки має бути від 0 до 100."}, status=400
                    )
            except ValueError:
                return JsonResponse(
                    {"error": "Відсоток знижки має бути числом."}, status=400
                )
        try:
            queries.execute(
                """UPDATE customer_card
                   SET cust_surname = %s, cust_name = %s, cust_patronymic = %s,
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
        except IntegrityError:
            return JsonResponse(
                {"error": "Помилка оновлення бази даних. Перевірте введені значення."},
                status=400,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        if request.session.get("role") != "Manager":
            return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)
        try:
            queries.execute(
                "DELETE FROM customer_card WHERE card_number = %s", [card_number]
            )
            return JsonResponse({"message": "Картку клієнта видалено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 4. PRODUCT VIEWS
# ==========================================


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "POST"])
def product_list_create(request):
    if request.method == "GET":
        category = request.GET.get("category")
        search = request.GET.get("search")

        query = """SELECT p.*, c.category_name FROM product p
                   JOIN category c ON p.category_number = c.category_number
                   WHERE 1=1"""
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

    if request.session.get("role") != "Manager":
        return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)

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
@login_required_api
@require_http_methods(["GET", "PUT", "DELETE"])
def product_detail(request, id_product):
    if request.method == "GET":
        product = queries.fetch_one(
            """SELECT p.*, c.category_name FROM product p
               JOIN category c ON p.category_number = c.category_number
               WHERE p.id_product = %s""",
            [id_product],
        )
        if not product:
            return JsonResponse({"error": "Товар не знайдено"}, status=404)
        return JsonResponse(product)

    if request.session.get("role") != "Manager":
        return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)

    if request.method == "PUT":
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
                {"error": "Неможливо видалити: товар уже є на вітрині."},
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 5. STORE PRODUCT VIEWS
# ==========================================


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "POST"])
def store_product_list_create(request):
    if request.method == "GET":
        # Keep the auto-promotion rule up to date before reading the list,
        # so products that have entered the 3-day expiry window show as on sale.
        queries.apply_expiry_promotions()

        promotional = request.GET.get("promotional")
        sort = validate_sort_column(request.GET.get("sort"), STORE_PROD_SORT_COLS)
        direction = "DESC" if request.GET.get("dir") == "desc" else "ASC"
        search = request.GET.get("search")

        query = (
            "SELECT sp.*, p.product_name, p.characteristics, c.category_name, "
            + ON_SALE_SQL.replace("expire_date", "sp.expire_date").replace(
                "products_number", "sp.products_number"
            )
            + """ AS on_sale
                   FROM store_product sp
                   JOIN product p ON sp.id_product = p.id_product
                   JOIN category c ON p.category_number = c.category_number
                   WHERE 1=1"""
        )
        params = []

        if promotional == "true":
            query += " AND sp.promotional_product = TRUE"
        elif promotional == "false":
            query += " AND sp.promotional_product = FALSE"
        if search:
            query += " AND p.product_name ILIKE %s"
            params.append(f"%{search}%")

        query += f" ORDER BY {sort} {direction}"
        products = queries.fetch_all(query, params)
        return JsonResponse({"results": products}, safe=False)

    if request.session.get("role") != "Manager":
        return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)

    data = json.loads(request.body)
    try:
        queries.execute(
            """INSERT INTO store_product ("UPC", "UPC_prom", id_product, selling_price, products_number, promotional_product, expire_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            [
                data["UPC"],
                data.get("UPC_prom"),
                data["id_product"],
                data["selling_price"],
                data["products_number"],
                data["promotional_product"],
                data.get("expire_date") or None,
            ],
        )
        queries.apply_expiry_promotions()
        return JsonResponse({"message": "Товар додано до магазину"}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "PUT", "DELETE"])
def store_product_detail(request, upc):
    if request.method == "GET":
        product = queries.fetch_one(
            "SELECT sp.*, p.product_name, p.characteristics, c.category_name, "
            + ON_SALE_SQL.replace("expire_date", "sp.expire_date").replace(
                "products_number", "sp.products_number"
            )
            + """ AS on_sale
               FROM store_product sp
               JOIN product p ON sp.id_product = p.id_product
               JOIN category c ON p.category_number = c.category_number
               WHERE sp."UPC" = %s""",
            [upc],
        )
        if not product:
            return JsonResponse({"error": "Товар не знайдено"}, status=404)
        return JsonResponse(product)

    if request.session.get("role") != "Manager":
        return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)

    if request.method == "PUT":
        data = json.loads(request.body)
        try:
            queries.execute(
                """UPDATE store_product
                   SET "UPC_prom" = %s, id_product = %s, selling_price = %s,
                       products_number = %s, promotional_product = %s, expire_date = %s
                   WHERE "UPC" = %s""",
                [
                    data.get("UPC_prom"),
                    data.get("id_product"),
                    data.get("selling_price"),
                    data.get("products_number"),
                    data.get("promotional_product"),
                    data.get("expire_date") or None,
                    upc,
                ],
            )
            queries.apply_expiry_promotions()
            return JsonResponse({"message": "Дані товару в магазині оновлено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "DELETE":
        try:
            queries.execute('DELETE FROM store_product WHERE "UPC" = %s', [upc])
            return JsonResponse({"message": "Товар видалено з магазину"})
        except IntegrityError:
            return JsonResponse(
                {"error": "Неможливо видалити: товар входить до складу чеків."},
                status=409,
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@manager_required
@require_http_methods(["POST"])
def store_product_receipt(request, upc):
    """Goods receipt (Надходження): a new batch of an existing store product
    arrives. The supplied quantity is added to the stock. If a new selling price
    is given, the WHOLE product is revalued — both the old and the new batch get
    the new selling price (per the requirements)."""
    data = json.loads(request.body)
    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Вкажіть коректну кількість"}, status=400)
    if quantity <= 0:
        return JsonResponse({"error": "Кількість має бути більшою за нуль"}, status=400)

    new_price = data.get("selling_price")
    if new_price is not None and new_price != "":
        if float(new_price) < 0:
            return JsonResponse({"error": "Ціна не може бути від'ємною"}, status=400)
    else:
        new_price = None

    try:
        with transaction.atomic():
            row = queries.fetch_one(
                'SELECT selling_price, products_number FROM store_product '
                'WHERE "UPC" = %s FOR UPDATE',
                [upc],
            )
            if not row:
                return JsonResponse({"error": "Товар не знайдено"}, status=404)

            if new_price is None:
                # Same price — just top up the stock with the new batch.
                queries.execute(
                    'UPDATE store_product SET products_number = products_number + %s '
                    'WHERE "UPC" = %s',
                    [quantity, upc],
                )
                final_price = float(row["selling_price"])
            else:
                # New price — revalue all units (old + new batch) to the new price.
                queries.execute(
                    'UPDATE store_product '
                    'SET products_number = products_number + %s, selling_price = %s '
                    'WHERE "UPC" = %s',
                    [quantity, new_price, upc],
                )
                final_price = float(new_price)

            queries.apply_expiry_promotions()
            new_total = row["products_number"] + quantity
        return JsonResponse({
            "message": "Надходження прийнято",
            "products_number": new_total,
            "selling_price": round(final_price, 2),
            "revalued": new_price is not None,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 6. CHECK VIEWS
# ==========================================


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "POST"])
def check_list_create(request):
    if request.method == "GET":
        role = request.session.get("role")
        session_emp = request.session.get("employee_id")

        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        query = """SELECT c.*, e.empl_surname, e.empl_name
                   FROM "check" c
                   JOIN employee e ON c.id_employee = e.id_employee
                   WHERE 1=1"""
        params = []

        if role == "Cashier":
            query += " AND c.id_employee = %s"
            params.append(session_emp)
        else:
            id_employee = request.GET.get("id_employee")
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

    # POST — create check
    if request.session.get("role") != "Cashier":
        return JsonResponse(
            {"error": "Здійснювати продаж товарів (створювати чеки) може лише Касир."},
            status=403,
        )

    data = json.loads(request.body)
    id_employee = request.session.get("employee_id")  # Тепер це 100% касир

    role = request.session.get("role")
    session_emp = request.session.get("employee_id")

    if role == "Cashier":
        id_employee = session_emp
    else:
        id_employee = data.get("id_employee") or session_emp

    check_number = data.get("check_number") or f"CH{uuid.uuid4().hex[:8].upper()}"
    card_number = data.get("card_number") or None
    print_date = data.get("print_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    products = data.get("products", [])

    if not products:
        return JsonResponse({"error": "Чек не може бути порожнім"}, status=400)

    try:
        with transaction.atomic():
            # If a loyalty card is supplied, its discount percent applies to the
            # whole check subtotal (this is what actually makes "sales" work).
            card_percent = 0
            if card_number:
                card = queries.fetch_one(
                    "SELECT percent FROM customer_card WHERE card_number = %s",
                    [card_number],
                )
                if not card:
                    raise Exception("Картку клієнта не знайдено.")
                card_percent = int(card["percent"])

            subtotal = 0
            processed_products = []

            for product in products:
                actual_product = queries.fetch_one(
                    "SELECT selling_price, products_number, "
                    + ON_SALE_SQL
                    + ' AS on_sale FROM store_product WHERE "UPC" = %s FOR UPDATE',
                    [product["UPC"]],
                )
                if not actual_product:
                    raise Exception(f"Товар з UPC {product['UPC']} не знайдено.")

                qty = int(product["product_number"])
                if actual_product["products_number"] < qty:
                    raise Exception(
                        f"Недостатньо товару {product['UPC']} на складі "
                        f"(є {actual_product['products_number']}, потрібно {qty})."
                    )

                # Expiry sale: on-sale products are charged 20% off the list price.
                list_price = float(actual_product["selling_price"])
                real_price = (
                    round(list_price * (1 - EXPIRY_SALE_DISCOUNT), 2)
                    if actual_product["on_sale"]
                    else list_price
                )
                subtotal += qty * real_price
                processed_products.append(
                    {
                        "UPC": product["UPC"],
                        "product_number": qty,
                        "selling_price": real_price,
                    }
                )

            discount_amount = round(subtotal * card_percent / 100.0, 2)
            sum_total = subtotal - discount_amount
            vat = sum_total * 0.2

            queries.execute(
                """INSERT INTO "check" (check_number, id_employee, card_number, print_date, sum_total, vat)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                [check_number, id_employee, card_number, print_date, sum_total, vat],
            )

            for pp in processed_products:
                queries.execute(
                    """INSERT INTO sale ("UPC", check_number, product_number, selling_price)
                       VALUES (%s, %s, %s, %s)""",
                    [
                        pp["UPC"],
                        check_number,
                        pp["product_number"],
                        pp["selling_price"],
                    ],
                )
                queries.execute(
                    'UPDATE store_product SET products_number = products_number - %s WHERE "UPC" = %s',
                    [pp["product_number"], pp["UPC"]],
                )

        return JsonResponse(
            {
                "message": "Чек успішно створено",
                "check_number": check_number,
                "subtotal": round(subtotal, 2),
                "card_percent": card_percent,
                "discount_amount": discount_amount,
                "sum_total": round(sum_total, 2),
                "vat": round(vat, 2),
            },
            status=201,
        )
    except IntegrityError:
        return JsonResponse(
            {"error": "Недостатньо товару на складі або невірні дані чека."},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required_api
@require_http_methods(["GET", "DELETE"])
def check_detail(request, check_number):
    if request.method == "GET":
        check = queries.fetch_one(
            """SELECT c.*, e.empl_surname, e.empl_name
               FROM "check" c
               JOIN employee e ON c.id_employee = e.id_employee
               WHERE c.check_number = %s""",
            [check_number],
        )
        if not check:
            return JsonResponse({"error": "Чек не знайдено"}, status=404)

        if request.session.get("role") == "Cashier" and check[
            "id_employee"
        ] != request.session.get("employee_id"):
            return JsonResponse({"error": "Доступ заборонено"}, status=403)

        items = queries.fetch_all(
            """SELECT s."UPC", s.product_number, s.selling_price, p.product_name
               FROM sale s
               JOIN store_product sp ON s."UPC" = sp."UPC"
               JOIN product p ON sp.id_product = p.id_product
               WHERE s.check_number = %s""",
            [check_number],
        )
        return JsonResponse({"check": check, "items": items})

    elif request.method == "DELETE":
        if request.session.get("role") != "Manager":
            return JsonResponse({"error": "Доступ лише для менеджерів"}, status=403)
        try:
            queries.execute(
                'DELETE FROM "check" WHERE check_number = %s', [check_number]
            )
            return JsonResponse({"message": "Чек видалено"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# ==========================================
# 7. REPORT VIEWS
# ==========================================


@require_http_methods(["GET"])
@manager_required
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
@manager_required
def report_product_volume(request):
    upc = request.GET.get("upc")
    start = request.GET.get("start")
    end = request.GET.get("end")

    query = """SELECT SUM(s.product_number) as total_volume
               FROM sale s
               JOIN "check" c ON s.check_number = c.check_number
               WHERE 1=1"""
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
@manager_required
def report_checks_in_period(request):
    """Чеки касира/усіх за період з позиціями."""
    id_employee = request.GET.get("id_employee")
    start = request.GET.get("start")
    end = request.GET.get("end")

    query = """
        SELECT c.check_number, c.print_date, c.sum_total, c.vat,
               e.empl_surname, e.empl_name,
               cc.cust_surname, cc.cust_name
        FROM "check" c
        JOIN employee e ON c.id_employee = e.id_employee
        LEFT JOIN customer_card cc ON c.card_number = cc.card_number
        WHERE 1=1
    """
    params = []

    if id_employee:
        query += " AND c.id_employee = %s"
        params.append(id_employee)
    if start:
        query += " AND c.print_date >= %s"
        params.append(start)
    if end:
        query += " AND c.print_date <= %s"
        params.append(end)

    query += " ORDER BY c.print_date DESC"
    checks = queries.fetch_all(query, params)

    for ch in checks:
        ch["items"] = queries.fetch_all(
            """SELECT s.product_number, s.selling_price, p.product_name, s."UPC"
               FROM sale s
               JOIN store_product sp ON s."UPC" = sp."UPC"
               JOIN product p ON sp.id_product = p.id_product
               WHERE s.check_number = %s""",
            [ch["check_number"]],
        )

    return JsonResponse({"results": checks})


@require_http_methods(["GET"])
@manager_required
def report_total_sold_per_product(request):
    start = request.GET.get("start")
    end = request.GET.get("end")

    query = """
        SELECT p.product_name, SUM(s.product_number) AS total_sold
        FROM product p
        INNER JOIN store_product sp ON p.id_product = sp.id_product
        INNER JOIN sale s ON sp."UPC" = s."UPC"
        INNER JOIN "check" c ON s.check_number = c.check_number
        WHERE 1=1
    """
    params = []

    if start:
        query += " AND c.print_date >= %s"
        params.append(start)
    if end:
        query += " AND c.print_date <= %s"
        params.append(end)

    query += " GROUP BY p.product_name ORDER BY total_sold DESC"
    return JsonResponse({"results": queries.fetch_all(query, params)})


@require_http_methods(["GET"])
@manager_required
def report_customers_served_by_all_cashiers(request):
    return JsonResponse({"results": queries.get_customers_served_by_all_cashiers()})


@require_http_methods(["GET"])
@manager_required
def report_top_cashiers(request):
    start = request.GET.get("start", "1970-01-01")
    end = request.GET.get("end", "2100-01-01")
    return JsonResponse({"results": queries.get_top_cashiers_for_period(start, end)})


@require_http_methods(["GET"])
@manager_required
def report_categories_all_products_sold(request):
    return JsonResponse({"results": queries.get_categories_with_all_products_sold()})


@require_http_methods(["GET"])
@manager_required
def report_total_sold_per_category(request):
    start = request.GET.get("start", "1970-01-01")
    end = request.GET.get("end", "2100-01-01")
    return JsonResponse({"results": queries.get_total_sold_per_category(start, end)})


@require_http_methods(["GET"])
@manager_required
def report_employees_served_all_customers(request):
    return JsonResponse(
        {"results": queries.get_employees_who_served_all_card_customers()}
    )


# ==========================================
# 8. UI DROPDOWNS
# ==========================================


@require_http_methods(["GET"])
@login_required_api
def ui_dropdowns(request, entity):
    entity_map = {
        "categories": (
            "SELECT category_number as id, category_name as name "
            "FROM category ORDER BY category_name"
        ),
        "employees": (
            "SELECT id_employee as id, CONCAT(empl_surname, ' ', empl_name) as name "
            "FROM employee ORDER BY empl_surname"
        ),
        "cashiers": (
            "SELECT id_employee as id, CONCAT(empl_surname, ' ', empl_name) as name "
            "FROM employee WHERE empl_role = 'Cashier' ORDER BY empl_surname"
        ),
        "products": (
            "SELECT id_product as id, product_name as name "
            "FROM product ORDER BY product_name"
        ),
        "customer-cards": (
            "SELECT card_number as id, "
            "CONCAT(cust_surname, ' ', cust_name, ' (-', percent, '%%)') as name, percent "
            "FROM customer_card ORDER BY cust_surname"
        ),
        "store-products": (
            """SELECT sp."UPC" as id,
                      CONCAT(p.product_name, ' [', sp."UPC", '] — ', sp.selling_price, ' грн') as name,
                      sp.selling_price, sp.products_number, p.product_name,
                      sp.promotional_product,
                      """
            + ON_SALE_SQL.replace("expire_date", "sp.expire_date").replace(
                "products_number", "sp.products_number"
            )
            + """ AS on_sale
               FROM store_product sp
               JOIN product p ON sp.id_product = p.id_product
               WHERE sp.products_number > 0
               ORDER BY p.product_name"""
        ),
    }

    query = entity_map.get(entity)
    if not query:
        return JsonResponse({"error": "Невідома сутність"}, status=400)

    results = queries.fetch_all(query)
    return JsonResponse({"results": results}, safe=False)


def validate_employee_dates(dob_str, dos_str):
    """Перевіряє, чи виповнилося працівнику 18 років на момент прийому на роботу."""
    if not dob_str or not dos_str:
        return None
    try:
        # Відрізаємо можливі години/хвилини, залишаємо YYYY-MM-DD
        dob = datetime.strptime(dob_str[:10], "%Y-%m-%d").date()
        dos = datetime.strptime(dos_str[:10], "%Y-%m-%d").date()
        age = dos.year - dob.year - ((dos.month, dos.day) < (dob.month, dob.day))

        if age < 18:
            return "Працівнику має бути не менше 18 років на дату прийняття на роботу."
        if dos < dob:
            return "Дата прийняття не може бути ранішою за дату народження."
    except ValueError:
        return "Неправильний формат дати."
    return None
