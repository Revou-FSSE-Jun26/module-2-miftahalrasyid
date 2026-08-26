"""
Locust load test simulating a sequential user journey:
1. GET all products
2. GET a single product by ID
3. POST a new order
4. GET the created order

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Then open http://localhost:8089 and configure:
    - Start users: 50
    - Ramp up: 10 users/second
    - Max users: 200
"""
from locust import HttpUser, task, between, SequentialTaskSet
import json


class UserJourney(SequentialTaskSet):
    """Sequential user journey: browse → view → order → check order."""

    product_id = None
    order_id = None
    token = None

    def on_start(self):
        """Login to get a JWT token before starting tasks."""
        # Try multiple test accounts
        accounts = [
            {"email": "funny.clown.1112@gmail.com", "password": "root1234"},
            {"email": "mike@gmail.com", "password": "Password1234"},
            {"email": "justin@gmail.com", "password": "Password1234"},
            {"email": "budi@gmail.com", "password": "Password1234"},
        ]
        import random
        account = random.choice(accounts)
        response = self.client.post("/api/v1/auth/login", json=account)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")

    def _auth_headers(self):
        """Return Authorization header dict."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task
    def get_all_products(self):
        """Step 1: Browse all products."""
        with self.client.get("/api/v1/products/", name="GET /products") as response:
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", [])
                if products:
                    self.product_id = products[0].get("id")

    @task
    def get_single_product(self):
        """Step 2: View a single product by ID."""
        if self.product_id:
            self.client.get(
                f"/api/v1/products/{self.product_id}",
                name="GET /products/{id}"
            )

    @task
    def create_order(self):
        """Step 3: Place a new order."""
        if not self.product_id or not self.token:
            return

        response = self.client.post(
            "/api/v1/orders/",
            json={
                "name": "load test order",
                "items": [{"product_id": self.product_id, "quantity": 1}]
            },
            headers=self._auth_headers(),
            name="POST /orders"
        )
        if response.status_code == 201:
            data = response.json()
            order_data = data.get("data", {})
            self.order_id = order_data.get("id")

    @task
    def get_created_order(self):
        """Step 4: Fetch the created order."""
        if self.order_id and self.token:
            self.client.get(
                f"/api/v1/orders/{self.order_id}",
                headers=self._auth_headers(),
                name="GET /orders/{id}"
            )


class ShopUser(HttpUser):
    """Simulated user with sequential task flow."""
    tasks = [UserJourney]
    wait_time = between(1, 3)
