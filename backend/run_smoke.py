#!/usr/bin/env python3
"""Start backend, run smoke tests, stop backend."""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = "http://localhost:8000/api/v1"

os.chdir(BACKEND_DIR)
env = os.environ.copy()
env["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://nutrimind:nutrimind_dev@localhost:5432/nutrimind"
)

log_file = open("backend_uvicorn.log", "w")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=log_file,
    stderr=log_file,
    env=env,
)
print(f"Backend PID: {proc.pid}")

for i in range(30):
    try:
        r = urllib.request.urlopen(f"{BASE}/health", timeout=3)
        d = json.loads(r.read())
        if d.get("success"):
            print("Backend READY")
            break
    except Exception:
        time.sleep(1)
else:
    print("Backend TIMEOUT")
    proc.terminate()
    sys.exit(1)

PASS, FAIL = 0, 0
results = []


def req(method, path, body=None, token=None, extra_headers=None):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        body_data = resp.read()
        try:
            parsed = json.loads(body_data)
        except json.JSONDecodeError:
            parsed = {"raw": body_data.decode()}
        return resp.status, parsed, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body_data = e.read()
        try:
            parsed = json.loads(body_data)
        except json.JSONDecodeError:
            parsed = {"raw": body_data.decode()}
        return e.code, parsed, dict(e.headers)
    except Exception as e:
        return 0, {"error": str(e)}, {}


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        results.append(f"  PASS  {name}")
    else:
        FAIL += 1
        results.append(f"  FAIL  {name}  {detail}")


CORS_H = {
    "Origin": "http://localhost:3000",
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "Authorization, Content-Type",
}

print("\n=== CORS ===")
s, b, h = req("OPTIONS", "/health", extra_headers=CORS_H)
check("OPTIONS /health", s in (200, 204))
check("Access-Control-Allow-Origin", "access-control-allow-origin" in h)
check(
    "Origin matches frontend", h.get("access-control-allow-origin", "") == "http://localhost:3000"
)

test_email = f"smoke_{uuid.uuid4().hex[:12]}@example.com"
test_pass = "Sm0keT3st!Pass"

print("\n=== Registration ===")
s, b, h = req("POST", "/auth/register", {"email": test_email, "password": test_pass})
check("Registration 201", s == 201, f"got {s}: {json.dumps(b)[:200]}")
check("success=True", isinstance(b, dict) and b.get("success") is True)
check("access_token present", "access_token" in b.get("data", {}))
check("No password in response", "password" not in json.dumps(b))
check("No password_hash", "password_hash" not in json.dumps(b))
access_token = b.get("data", {}).get("access_token", "")

s, b, h = req("POST", "/auth/register", {"email": test_email, "password": test_pass})
check("Duplicate 409", s == 409, f"got {s}")
check(
    "EMAIL_ALREADY_REGISTERED",
    isinstance(b, dict) and b.get("error", {}).get("code") == "EMAIL_ALREADY_REGISTERED",
)

print("\n=== Login ===")
s, b, h = req("POST", "/auth/login", {"email": test_email, "password": test_pass})
check("Login 200", s == 200, f"got {s}")
access_token = b.get("data", {}).get("access_token", "")

s, b, h = req("POST", "/auth/login", {"email": test_email, "password": "wrong"})
check("Wrong pw 401", s == 401, f"got {s}")
check(
    "INVALID_CREDENTIALS",
    isinstance(b, dict) and b.get("error", {}).get("code") == "INVALID_CREDENTIALS",
)

s, b, h = req("POST", "/auth/login", {"email": "no@no.com", "password": test_pass})
check("Unknown account 401", s == 401, f"got {s}")

print("\n=== Auth Errors ===")
s, b, h = req("GET", "/auth/me")
check("No token 401", s == 401, f"got {s}")
check(
    "AUTHENTICATION_REQUIRED",
    isinstance(b, dict) and b.get("error", {}).get("code") == "AUTHENTICATION_REQUIRED",
)

s, b, h = req("GET", "/auth/me", token="badtoken")
check("Bad token 401", s == 401, f"got {s}")
check(
    "INVALID_ACCESS_TOKEN",
    isinstance(b, dict) and b.get("error", {}).get("code") == "INVALID_ACCESS_TOKEN",
)

s, b, h = req("GET", "/auth/me", token=access_token)
check("GET /auth/me 200", s == 200, f"got {s}")
check("Email matches", isinstance(b, dict) and b.get("data", {}).get("email") == test_email)

print("\n=== Nutrition Profile ===")
s, b, h = req("GET", "/nutrition-profile", token=access_token)
check("Missing profile 404", s == 404, f"got {s}")

profile = {
    "date_of_birth": "1990-01-15",
    "biological_sex": "male",
    "height_cm": 175.0,
    "weight_kg": 80.0,
    "activity_level": "moderately_active",
    "goal": "lose_weight",
    "target_weight_kg": 70.0,
}
s, b, h = req("POST", "/nutrition-profile", profile, token=access_token)
check("Create profile 201", s == 201, f"got {s}: {json.dumps(b)[:200]}")

s, b, h = req("GET", "/nutrition-profile", token=access_token)
check("Get profile 200", s == 200, f"got {s}")
p = b.get("data", {}).get("profile", {})
check("sex=male", p.get("biological_sex") == "male")
check("height=175.00", p.get("height_cm") == "175.00")
check("goal=lose_weight", p.get("goal") == "lose_weight")

print("\n=== Calculations/Summary ===")
s, b, h = req(
    "GET", "/nutrition-profile/calculations?reference_date=2026-07-14", token=access_token
)
check("Calculations 200", s == 200, f"got {s}")
s, b, h = req("GET", "/nutrition-profile/summary?reference_date=2026-07-14", token=access_token)
check("Summary 200", s == 200, f"got {s}")

print("\n=== Update Profile ===")
s, b, h = req("PATCH", "/nutrition-profile", {"height_cm": 176.0}, token=access_token)
check("Update 200", s == 200, f"got {s}")
s, b, h = req("GET", "/nutrition-profile", token=access_token)
check("Updated height", b.get("data", {}).get("profile", {}).get("height_cm") == "176.00")

print("\n=== Nutrition Logs ===")
log_entry_id = str(uuid.uuid4())
log_entry = {
    "entry_id": log_entry_id,
    "food_name": "Test Breakfast",
    "meal_type": "breakfast",
    "serving_description": "1 bowl",
    "calories_kcal": 350.0,
    "protein_g": 15.0,
    "carbohydrate_g": 45.0,
    "fat_g": 12.0,
}
s, b, h = req("POST", "/nutrition-logs?logged_date=2026-07-14", log_entry, token=access_token)
check("Create log 201", s == 201, f"got {s}: {json.dumps(b)[:200]}")
entry_id = b.get("data", {}).get("entry_id", "")
check("entry_id returned", bool(entry_id))

s, b, h = req("GET", "/nutrition-logs?logged_date=2026-07-14", token=access_token)
check("List logs 200", s == 200, f"got {s}")
entries = b.get("data", {}).get("entries", [])
check("Entry in list", any(e.get("entry_id") == entry_id for e in entries))

s, b, h = req("GET", "/nutrition-logs/summary?logged_date=2026-07-14", token=access_token)
check("Daily summary 200", s == 200, f"got {s}")

s, b, h = req(
    "GET",
    "/nutrition-logs/progress?logged_date=2026-07-14&reference_date=2026-07-14",
    token=access_token,
)
check("Target progress 200", s == 200, f"got {s}")

s, b, h = req("DELETE", f"/nutrition-logs/{entry_id}", token=access_token)
check("Delete log 200", s == 200, f"got {s}")

s, b, h = req("GET", "/nutrition-logs?logged_date=2026-07-14", token=access_token)
entries = b.get("data", {}).get("entries", [])
check("Deleted entry absent", not any(e.get("entry_id") == entry_id for e in entries))

print("\n=== Body Weight ===")
s, b, h = req(
    "POST", "/body-weights?logged_date=2026-07-01", {"weight_kg": 80.5}, token=access_token
)
check("Create BW 1 201", s == 201, f"got {s}")

s, b, h = req("GET", "/body-weights/trend", token=access_token)
check("Trend 1 entry 422", s == 422, f"got {s}")

s, b, h = req(
    "POST", "/body-weights?logged_date=2026-07-08", {"weight_kg": 79.0}, token=access_token
)
check("Create BW 2 201", s == 201, f"got {s}")

s, b, h = req("GET", "/body-weights", token=access_token)
check("History 200", s == 200, f"got {s}")
bw_entries = b.get("data", {}).get("entries", [])
check(">=2 BW entries", len(bw_entries) >= 2, str(len(bw_entries)))

s, b, h = req("GET", "/body-weights/trend", token=access_token)
check("Trend 200", s == 200, f"got {s}")

s, b, h = req("GET", "/body-weights/goal-progress", token=access_token)
check("Goal progress 200", s == 200, f"got {s}")

for e in bw_entries:
    s, b, h = req("DELETE", f"/body-weights/{e['entry_id']}", token=access_token)
    check("Delete BW 200", s == 200, f"got {s}")

s, b, h = req("GET", "/body-weights", token=access_token)
check("History empty", b.get("data", {}).get("count", 0) == 0)

print("\n=== Tasks ===")
s, b, h = req("POST", "/tasks", {"title": "Smoke Test", "priority": "high"}, token=access_token)
check("Create task 201", s == 201, f"got {s}: {json.dumps(b)[:200]}")
task_id = b.get("data", {}).get("task_id", "")

s, b, h = req("GET", "/tasks", token=access_token)
check("List tasks 200", s == 200, f"got {s}")
check("Task in list", any(t.get("task_id") == task_id for t in b.get("data", {}).get("tasks", [])))

s, b, h = req("GET", f"/tasks/{task_id}", token=access_token)
check("Get task 200", s == 200, f"got {s}")
check("Title match", b.get("data", {}).get("title") == "Smoke Test")

s, b, h = req(
    "POST",
    f"/tasks/{task_id}/complete",
    {"completed_at": "2026-07-14T12:00:00"},
    token=access_token,
)
check("Complete 200", s == 200, f"got {s}")
check("Status completed", b.get("data", {}).get("status") == "completed")

s, b, h = req("POST", f"/tasks/{task_id}/reopen", token=access_token)
check("Reopen 200", s == 200, f"got {s}")
check("Status pending", b.get("data", {}).get("status") == "pending")

s, b, h = req("DELETE", f"/tasks/{task_id}", token=access_token)
check("Delete 200", s == 200, f"got {s}")

s, b, h = req("GET", f"/tasks/{task_id}", token=access_token)
check("Deleted task 404", s == 404, f"got {s}")

print("\n=== User Isolation ===")
email_b = f"smoke_b_{uuid.uuid4().hex[:12]}@example.com"
s, b, h = req("POST", "/auth/register", {"email": email_b, "password": "Sm0keB!Pass"})
token_b = b.get("data", {}).get("access_token", "")

s, b, h = req("POST", "/tasks", {"title": "B Task"}, token=token_b)
b_task_id = b.get("data", {}).get("task_id", "")

s, b, h = req("GET", f"/tasks/{b_task_id}", token=access_token)
check("A can't access B's task 404", s == 404, f"got {s}")

s, b, h = req("DELETE", f"/tasks/{b_task_id}", token=access_token)
check("A can't delete B's task 404", s == 404, f"got {s}")

req("DELETE", f"/tasks/{b_task_id}", token=token_b)

print("\n=== Privacy ===")
for ep in ["/auth/me", "/nutrition-profile", "/tasks", "/body-weights"]:
    _, b, _ = req("GET", ep, token=access_token)
    bstr = json.dumps(b)
    check(f"No password_hash in {ep}", "password_hash" not in bstr)
    check(f"No stack trace in {ep}", "Traceback" not in bstr)

print("\n=== Request ID ===")
for ep in ["/health", "/auth/me"]:
    _, _, hdrs = req("GET", ep, token=access_token if ep != "/health" else None)
    check(f"X-Request-ID in {ep}", "x-request-id" in hdrs and bool(hdrs.get("x-request-id", "")))

print(f"\n{'=' * 60}")
print(f"  TOTAL: {PASS} passed, {FAIL} failed")
print(f"{'=' * 60}")
for r in results:
    print(r)

proc.terminate()
proc.wait()
log_file.close()

sys.exit(0 if FAIL == 0 else 1)
