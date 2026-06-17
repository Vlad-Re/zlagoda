"""Django models — used ONLY to define tables and run migrations.

These models describe the database schema so that `makemigrations` / `migrate`
can create the tables. They are NOT used for queries: all reads and writes go
through raw SQL in `core/db.py`.

Foreign-key `on_delete` here only satisfies Django's field API — it is enforced
by the ORM in Python and does not apply to our raw-SQL writes. The real,
database-level update/delete policies are declared in `core/constraints.py` and
applied with `python manage.py apply_constraints` after migrating.

Example:

    class Category(models.Model):
        category_number = models.AutoField(primary_key=True)
        category_name = models.CharField(max_length=50, unique=True)

        class Meta:
            db_table = "category"
"""

from django.db import models  # noqa: F401

class Category(models.Model):
    category_number = models.IntegerField(primary_key=True)
    category_name = models.CharField(max_length=50)

    class Meta:
        db_table = "category"


class Product(models.Model):
    id_product = models.IntegerField(primary_key=True)
    category_number = models.ForeignKey(
        'Category',
        on_delete=models.DO_NOTHING,
        db_column='category_number'
    )
    product_name = models.CharField(max_length=50)
    characteristics = models.CharField(max_length=100)

    class Meta:
        db_table = "product"


class StoreProduct(models.Model):
    UPC = models.CharField(max_length=12, primary_key=True)
    UPC_prom = models.ForeignKey(
        'self',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column='UPC_prom'
    )
    id_product = models.ForeignKey(
        'Product',
        on_delete=models.DO_NOTHING,
        db_column='id_product'
    )
    selling_price = models.DecimalField(max_digits=13, decimal_places=4)
    products_number = models.IntegerField()
    promotional_product = models.BooleanField()
    expire_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "store_product"


class Employee(models.Model):
    id_employee = models.CharField(max_length=10, primary_key=True)
    empl_surname = models.CharField(max_length=50)
    empl_name = models.CharField(max_length=50)
    empl_patronymic = models.CharField(max_length=50, null=True, blank=True)
    empl_role = models.CharField(max_length=10)
    salary = models.DecimalField(max_digits=13, decimal_places=4)
    date_of_birth = models.DateField()
    date_of_start = models.DateField()
    phone_number = models.CharField(max_length=13)
    city = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=9)
    password_hash = models.CharField(max_length=128, default='')

    class Meta:
        db_table = "employee"


class CustomerCard(models.Model):
    card_number = models.CharField(max_length=13, primary_key=True)
    cust_surname = models.CharField(max_length=50)
    cust_name = models.CharField(max_length=50)
    cust_patronymic = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=13)
    city = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.CharField(max_length=9, null=True, blank=True)
    percent = models.IntegerField()

    class Meta:
        db_table = "customer_card"


class Check(models.Model):
    check_number = models.CharField(max_length=10, primary_key=True)
    id_employee = models.ForeignKey(
        'Employee',
        on_delete=models.DO_NOTHING,
        db_column='id_employee'
    )
    card_number = models.ForeignKey(
        'CustomerCard',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        db_column='card_number'
    )
    print_date = models.DateTimeField()
    sum_total = models.DecimalField(max_digits=13, decimal_places=4)
    vat = models.DecimalField(max_digits=13, decimal_places=4)

    class Meta:
        db_table = "check"


class Sale(models.Model):
    UPC = models.ForeignKey(
        'StoreProduct',
        on_delete=models.DO_NOTHING,
        db_column='UPC'
    )
    check_number = models.ForeignKey(
        'Check',
        on_delete=models.DO_NOTHING,
        db_column='check_number'
    )
    product_number = models.IntegerField()
    selling_price = models.DecimalField(max_digits=13, decimal_places=4)

    class Meta:
        db_table = "sale"
        unique_together = (('UPC', 'check_number'),)