import httpx
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
UID = str(int(time.time()))
EMAIL = f"qa_user_{UID}@example.com"
PASSWORD = "Password123!"

print(f"=== REGISTERING USER: {EMAIL} ===")
reg_resp = httpx.post(f"{BASE_URL}/auth/register", json={
    "email": EMAIL,
    "password": PASSWORD
})

if reg_resp.status_code >= 400:
    print("Registration Failed:", reg_resp.json())
    exit(1)

print("=== LOGGING IN ===")
login_resp = httpx.post(f"{BASE_URL}/auth/login", json={
    "email": EMAIL,
    "password": PASSWORD
})

if login_resp.status_code != 200:
    print("Login Failed:", login_resp.json())
    exit(1)

token = login_resp.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== IMPORTING JSON FILE ===")
files = {
    'file': ('nutrimind-full-profile-test.json', open('c:/Users/Sai Adithya/Downloads/nutrimind-full-profile-test.json', 'rb'), 'application/json')
}
import_resp = httpx.post(f"{BASE_URL}/settings/import", headers=headers, files=files)

print("Import Response Status:", import_resp.status_code)
if import_resp.status_code >= 400:
    print("Import Failed:", import_resp.text)
else:
    print("Import Success:", import_resp.json())

print("=== VERIFYING TASKS ===")
tasks_resp = httpx.get(f"{BASE_URL}/tasks", headers=headers)
print("Tasks Response:", tasks_resp.status_code)
resp_json = tasks_resp.json()
tasks = resp_json.get("data", resp_json)
if isinstance(tasks, dict):
    tasks = tasks.get("tasks", [])
print(f"Loaded {len(tasks)} tasks.")

all_valid = True
for t in tasks:
    if t["status"] == "completed":
        if not t.get("completed_at"):
            print(f"ERROR: Task {t['id']} is completed but completed_at is NULL!")
            all_valid = False
        else:
            print(f"OK: Task '{t['title']}' is completed and completed_at = {t['completed_at']}")

if all_valid:
    print("ALL IMPORTED TASKS HAVE CORRECT completed_at INVARIANTS.")

print("=== VERIFYING GOALS ===")
goals_resp = httpx.get(f"{BASE_URL}/goals", headers=headers)
print("Goals Response:", goals_resp.status_code)
g_json = goals_resp.json()
goals = g_json.get("data", g_json) if isinstance(g_json, dict) else g_json
if isinstance(goals, dict):
    goals = goals.get("goals", [])
print(f"Loaded {len(goals)} goals.")
print("=== DONE ===")
