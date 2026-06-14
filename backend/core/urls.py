from django.urls import path
from . import views

urlpatterns = [
    path("categories/", views.category_list_create, name="categories-list"),
    path(
        "categories/<int:category_number>/",
        views.category_detail,
        name="category-detail",
    ),
    path("employees/", views.employee_list_create, name="employees-list"),
    path("employees/<str:id_employee>/", views.employee_detail, name="employee-detail"),
    path("customer-cards/", views.customer_card_list_create, name="cards-list"),
    path(
        "customer-cards/<str:card_number>/",
        views.customer_card_detail,
        name="card-detail",
    ),
    path("products/", views.product_list_create, name="products-list"),
    path("products/<int:id_product>/", views.product_detail, name="product-detail"),
    path(
        "store-products/", views.store_product_list_create, name="store-products-list"
    ),
    path(
        "store-products/<str:upc>/",
        views.store_product_detail,
        name="store-product-detail",
    ),
    path("checks/", views.check_list_create, name="checks-list"),
    path("checks/<str:check_number>/", views.check_detail, name="check-detail"),
    path(
        "reports/sales-revenue/",
        views.report_sales_revenue,
        name="report-sales-revenue",
    ),
    path(
        "reports/product-volume/",
        views.report_product_volume,
        name="report-product-volume",
    ),
    path("ui/dropdowns/<str:entity>/", views.ui_dropdowns, name="ui-dropdowns"),
]
