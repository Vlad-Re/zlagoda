import json
from core import queries
from .test_base import BaseZlagodaTest


class CheckTransactionTests(BaseZlagodaTest):
    def setUp(self):
        super().setUp()
        queries.execute("DELETE FROM store_product")
        queries.execute(
            """INSERT INTO store_product ("UPC", id_product, selling_price, products_number, promotional_product)
               VALUES ('123456789012', 100, 40.00, 10, FALSE)"""
        )

    def test_successful_check_creation(self):
        """Test successful check creation (product deduction and correct sum calculation)."""
        payload = {
            "check_number": "CHK001",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "123456789012", "product_number": 3}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CHK001'"
        )
        self.assertIsNotNone(check)
        self.assertEqual(float(check["sum_total"]), 120.00)

        product_in_store = queries.fetch_one(
            "SELECT products_number FROM store_product WHERE \"UPC\" = '123456789012'"
        )
        self.assertEqual(product_in_store["products_number"], 7)

    def test_failed_transaction_rollback_due_to_amount(self):
        """Test ACID: attempt to sell more than available in store."""
        payload = {
            "check_number": "CHK002",
            "id_employee": "EMP_TEST",
            "products": [{"UPC": "123456789012", "product_number": 15}],
        }

        response = self.client.post(
            "/api/checks/", data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        check = queries.fetch_one(
            "SELECT * FROM \"check\" WHERE check_number = 'CHK002'"
        )
        self.assertIsNone(check)

        product_in_store = queries.fetch_one(
            "SELECT products_number FROM store_product WHERE \"UPC\" = '123456789012'"
        )
        self.assertEqual(product_in_store["products_number"], 10)
