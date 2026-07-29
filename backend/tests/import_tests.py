"""
Import format examples and test fixtures for Data Center import.
These examples match the CSV/JSON/TXT parsers in app/api/v1/settings.py.

Structured CSV (3 columns: Section, Field, Value)
--------------------------------------------------
Detected when ANY data row's first column contains a keyword
(Profile, BodyWeight, FoodLog, Task). Header rows with
"Section,Key,Value" or "Title,Status,Due" are ignored.

Supported sections:
  Profile     -> Field,Value  (date_of_birth, biological_sex, height_cm, weight_kg)
  BodyWeight  -> logged_date, weight_kg (e.g. "2024-01-01", "78.5 kg")
  FoodLog     -> logged_date+meal_type, "food_name - calories_kcal"
  Task        -> status, "title" or "title - Due: YYYY-MM-DD"
"""

# =============================================================================
# EXAMPLE 1 — Structured CSV with header row (the format that was broken)
# =============================================================================

CSV_WITH_SECTION_HEADER = """\
Section,Key,Value
Profile,date_of_birth,1990-06-15
Profile,biological_sex,male
Profile,height_cm,178
Profile,weight_kg,75
BodyWeight,2024-01-01,78.5 kg
BodyWeight,2024-01-15,77.0 kg
FoodLog,2024-01-01 breakfast,Oatmeal - 350 kcal
FoodLog,2024-01-01 lunch,Chicken Salad - 450 kcal
Task,pending,Buy groceries
Task,completed,Finished project report
Task,pending,Read 30 minutes
"""

# Expected parse result:
#   profile: 1 (date_of_birth="1990-06-15", biological_sex="male", ...)
#   body_weights: 2 (2024-01-01 -> 78.5, 2024-01-15 -> 77.0)
#   nutrition_logs: 2 (breakfast Oatmeal, lunch Chicken Salad)
#   tasks: 3 (Buy groceries, Finished project report, Read 30 minutes)

# =============================================================================
# EXAMPLE 2 — Structured CSV without header (first row is data)
# =============================================================================

CSV_DIRECT_STRUCTURED = """\
BodyWeight,2024-06-01,72.0 kg
BodyWeight,2024-06-15,71.5 kg
FoodLog,2024-06-01 breakfast,Scrambled eggs - 300 kcal
FoodLog,2024-06-01 lunch,Quinoa bowl - 500 kcal
Task,pending,Complete workout
Task,completed,Write report
"""

# Expected parse result:
#   body_weights: 2
#   nutrition_logs: 2
#   tasks: 2

# =============================================================================
# EXAMPLE 3 — Simple CSV (2 columns: status/title or date/weight)
# =============================================================================

CSV_SIMPLE = """\
pending,Water the plants
completed,Call dentist
2024-03-01,80.0 kg
2024-03-15,79.5 kg
"""

# Expected parse result:
#   body_weights: 2 (date rows detected)
#   tasks: 2 (non-date rows treated as status,task)

# =============================================================================
# EXAMPLE 4 — JSON (all supported entities)
# =============================================================================

JSON_FULL = """\
{
  "profile": {
    "date_of_birth": "1995-03-10",
    "biological_sex": "male",
    "height_cm": 178,
    "weight_kg": 75
  },
  "body_weights": [
    {"logged_date": "2026-07-10", "weight_kg": 75.0},
    {"logged_date": "2026-07-15", "weight_kg": 74.5},
    {"logged_date": "2026-07-20", "weight_kg": 74.0}
  ],
  "nutrition_logs": [
    {"logged_date": "2026-07-20 breakfast", "food_name": "Oatmeal", "calories_kcal": 300},
    {"logged_date": "2026-07-20 lunch", "food_name": "Salad", "calories_kcal": 400}
  ],
  "tasks": [
    {"title": "Task 1", "status": "pending", "priority": "high"},
    {"title": "Completed task", "status": "completed", "priority": "medium",
     "completed_at": "2026-07-19T10:00:00Z"},
    {"title": "Task 3", "status": "pending", "priority": "low"}
  ],
  "goals": [
    {
      "goal_type": "weight_loss",
      "title": "Lose 5 kg",
      "description": "Gradual weight loss",
      "start_date": "2026-07-01",
      "end_date": "2026-09-30",
      "weekly_target": 0.5,
      "target_calories": 2000,
      "target_protein": 150,
      "target_carbs": 200,
      "target_fats": 65,
      "target_water": 2000
    }
  ]
}
"""

# Expected parse result:
#   profile: 1
#   body_weights: 3
#   nutrition_logs: 2
#   tasks: 3
#   goals: 1

# =============================================================================
# EXAMPLE 5 — TXT (same parser as CSV, structured 3-column format)
# =============================================================================

TXT_STRUCTURED = """\
BodyWeight,2026-07-25,73.0 kg
FoodLog,2026-07-25 breakfast,TXT Oatmeal - 300 kcal
Task,pending,TXT Import Task
"""

# Expected parse result:
#   body_weights: 1
#   nutrition_logs: 1
#   tasks: 1

# =============================================================================
# EXAMPLE 6 — Edge cases
# =============================================================================

# Completed task WITHOUT completed_at — backend auto-sets to now
CSV_COMPLETED_TASK = """\
Task,completed,Completed task without timestamp
"""

# Duplicate data — second import skips matching records
CSV_DUPLICATE = """\
BodyWeight,2024-01-01,78.5 kg
Task,pending,Buy groceries
"""

# Malformed JSON — returns 400 with "Invalid JSON format."
JSON_MALFORMED = """\
{ "this is "not valid" }
"""

# Empty file — returns 200 with zero counts
CSV_EMPTY = ""
