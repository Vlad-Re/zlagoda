import json
from .test_base import BaseZlagodaTest


class ReportTests(BaseZlagodaTest):
    def test_ui_dropdowns_endpoint(self):
        """Test auxiliary endpoint for forming dropdown lists."""
        response = self.client.get("/api/ui/dropdowns/categories/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("id", data["results"][0])
        self.assertIn("name", data["results"][0])

    # Tests for get_top_cashiers_for_period etc. can be added here,
    # after generating several checks in setUp.
