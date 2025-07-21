from locust import HttpUser, SequentialTaskSet, task, between
import random
import json

class UserBehavior(SequentialTaskSet):

    def on_start(self):
        # Login once per simulated user
        response = self.client.post("/login", data={"username": "testuser", "password": "testpass"}, allow_redirects=False)
        # Assume session cookie is set automatically

        # Setup some test data IDs (replace with real ones)
        self.test_item_ids = [1, 2, 3]
        self.test_habit_ids = []
        self.test_receiver_ids = [5, 6]
        self.test_request_ids = []

    @task
    def view_calendar(self):
        self.client.get("/")

    @task
    def create_habit(self):
        habit_data = {
            "title": "Test Habit",
            "category_id": 1
        }
        response = self.client.post("/create_habit", data=habit_data)
        # Optional: Check if redirect happened (status 302), indicating success
        if response.status_code == 302:
            print("Habit created successfully")
        else:
            print(f"Failed to create habit: {response.status_code} - {response.text}")


    @task
    def visit_shop(self):
        self.client.get("/shop")

    @task
    def purchase_item(self):
        item_id = random.choice(self.test_item_ids)
        self.client.post(f"/buy_item/{item_id}")

    @task
    def use_item(self):
        item_id = random.choice(self.test_item_ids)
        self.client.post(f"/use_item/{item_id}")

    @task
    def view_community(self):
        self.client.get("/community")

    @task
    def send_friend_request(self):
        receiver_id = random.choice(self.test_receiver_ids)
        response = self.client.post(f"/send_friend_request/{receiver_id}")
        # You could parse response to get friend request ID, but assuming test_request_ids known
        # For demo, let's just add a fake request id
        self.test_request_ids.append(100)

    @task
    def visit_inbox(self):
        self.client.get("/inbox")

    @task
    def accept_friend_request(self):
        if not self.test_request_ids:
            return  # No requests to accept
        request_id = self.test_request_ids.pop()
        payload = {"action": "accept"}
        self.client.post(f"/respond_friend_request/{request_id}", json=payload)

class MyAppUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 3)
