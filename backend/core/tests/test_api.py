import json
from .test_base import BaseZlagodaTest


class ApiCrudTests(BaseZlagodaTest):
    def test_get_categories(self):
        """Test getting the list of categories."""
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(len(data["results"]) >= 1)
        self.assertEqual(data["results"][0]["category_name"], "Тестова категорія")

    def test_create_employee_under_18_fails(self):
        """Test semantic constraint chk_emp_age (employee < 18 years)."""
        payload = {
            "id_employee": "EMP_YOUTH",
            "empl_surname": "Молодий",
            "empl_name": "Петро",
            "empl_role": "Cashier",
            "salary": 10000,
            "date_of_birth": "2020-01-01",  # Obviously less than 18 years
            "date_of_start": "2026-06-15",
            "phone_number": "+380123456789",
            "city": "Київ",
            "street": "Вулиця",
            "zip_code": "00000",
        }

        response = self.client.post(
            "/api/employees/", data=json.dumps(payload), content_type="application/json"
        )

        # Expect 400 Bad Request, since DB constraint will reject the record
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Constraint violation", data["error"])
