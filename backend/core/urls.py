from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("auth/login", views.login_view, name="auth-login"),
    path("auth/logout", views.logout_view, name="auth-logout"),
    path("auth/me", views.me_view, name="auth-me"),

    # Categories
    path("categories/", views.category_list_create, name="categories-list"),
    path("categories/<int:category_number>/", views.category_detail, name="category-detail"),

    # Employees
    path("employees/", views.employee_list_create, name="employees-list"),
    path("employees/search/", views.employee_search, name="employee-search"),
    path("employees/<str:id_employee>/", views.employee_detail, name="employee-detail"),

    # Customer cards
    path("customer-cards/", views.customer_card_list_create, name="cards-list"),
    path("customer-cards/<str:card_number>/", views.customer_card_detail, name="card-detail"),

    # Products
    path("products/", views.product_list_create, name="products-list"),
    path("products/<int:id_product>/", views.product_detail, name="product-detail"),

    # Store products
    path("store-products/", views.store_product_list_create, name="store-products-list"),
    path("store-products/<str:upc>/", views.store_product_detail, name="store-product-detail"),

    # Checks
    path("checks/", views.check_list_create, name="checks-list"),
    path("checks/<str:check_number>/", views.check_detail, name="check-detail"),

    # Reports
    path("reports/sales-revenue/", views.report_sales_revenue, name="report-sales-revenue"),
    path("reports/product-volume/", views.report_product_volume, name="report-product-volume"),
    path("reports/checks-in-period/", views.report_checks_in_period, name="report-checks-in-period"),
    path("reports/total-sold-per-product/", views.report_total_sold_per_product, name="report-total-sold-per-product"),
    path("reports/customers-served-by-all-cashiers/", views.report_customers_served_by_all_cashiers, name="report-customers-served-by-all-cashiers"),
    path("reports/top-cashiers/", views.report_top_cashiers, name="report-top-cashiers"),
    path("reports/categories-all-products-sold/", views.report_categories_all_products_sold, name="report-categories-all-products-sold"),
    path("reports/total-sold-per-category/", views.report_total_sold_per_category, name="report-total-sold-per-category"),
    path("reports/employees-served-all-customers/", views.report_employees_served_all_customers, name="report-employees-served-all-customers"),

    # UI helpers
    path("ui/dropdowns/<str:entity>/", views.ui_dropdowns, name="ui-dropdowns"),
]
