from __future__ import annotations

import csv
import io
import json
import logging
import uuid as uuid_lib
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_user
from app.core.middleware import get_request_id
from app.core.tasks import TaskPriority
from app.db.dependencies import get_db_session
from app.models.body_weight import BodyWeight
from app.models.nutrition_log import NutritionLog
from app.models.nutrition_profile import NutritionProfile
from app.models.task import Task
from app.models.goal import Goal
from app.models.enums import GoalType
from decimal import Decimal
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["Settings"])


@router.delete("/account")
async def delete_account(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    request_id = get_request_id() or "-"
    try:
        await session.delete(current_user)
        await session.commit()
        return {"success": True, "message": "Account and all associated data permanently deleted."}
    except Exception as exc:
        await session.rollback()
        logger.exception("Account deletion failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"Account deletion failed: {str(exc)}"},
        )


EXPORT_FORMATS = Literal["csv", "xlsx", "json", "pdf", "txt"]


@router.get("/export")
async def export_data(
    request: Request,
    format: str = Query("json", description="Export format: csv, xlsx, json, pdf, txt"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    request_id = get_request_id() or "-"

    if format not in ("csv", "xlsx", "json", "pdf", "txt"):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": f"Unsupported export format: {format}. Supported: csv, xlsx, json, pdf, txt."},
        )

    try:
        stmt_profile = select(NutritionProfile).where(NutritionProfile.user_id == current_user.id)
        result = await session.execute(stmt_profile)
        profile = result.scalars().one_or_none()

        stmt_bw = select(BodyWeight).where(BodyWeight.user_id == current_user.id).order_by(BodyWeight.logged_date)
        result = await session.execute(stmt_bw)
        body_weights = result.scalars().all()

        stmt_nl = select(NutritionLog).where(NutritionLog.user_id == current_user.id).order_by(NutritionLog.logged_date)
        result = await session.execute(stmt_nl)
        nutrition_logs = result.scalars().all()

        stmt_tasks = select(Task).where(Task.user_id == current_user.id).order_by(Task.created_at)
        result = await session.execute(stmt_tasks)
        tasks = result.scalars().all()

        stmt_goals = select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.created_at)
        result = await session.execute(stmt_goals)
        goals = result.scalars().all()

        if format == "json":
            data_dict = {
                "profile": {
                    "date_of_birth": str(profile.date_of_birth) if profile and profile.date_of_birth else None,
                    "biological_sex": profile.biological_sex if profile and profile.biological_sex else None,
                    "height_cm": float(profile.height_cm) if profile and profile.height_cm is not None else None,
                    "weight_kg": float(profile.weight_kg) if profile and profile.weight_kg is not None else None,
                } if profile else None,
                "body_weights": [
                    {"logged_date": str(b.logged_date), "weight_kg": float(b.weight_kg)}
                    for b in body_weights
                ],
                "nutrition_logs": [
                    {
                        "logged_date": f"{nl.logged_date} {nl.meal_type}",
                        "food_name": nl.food_name,
                        "calories_kcal": float(nl.calories_kcal),
                    }
                    for nl in nutrition_logs
                ],
                "tasks": [
                    {
                        "title": t.title,
                        "status": t.status.value if t.status else "pending",
                        "priority": t.priority.value if t.priority else "medium",
                        "due_date": str(t.due_date) if t.due_date else None,
                        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    }
                    for t in tasks
                ],
                "goals": [
                    {
                        "goal_type": g.goal_type.value if g.goal_type else "weight_loss",
                        "title": g.title,
                        "description": g.description,
                        "start_date": str(g.start_date) if g.start_date else None,
                        "end_date": str(g.end_date) if g.end_date else None,
                        "weekly_target": float(g.weekly_target) if g.weekly_target is not None else None,
                        "target_calories": g.target_calories,
                        "target_protein": g.target_protein_g,
                        "target_carbs": g.target_carbs_g,
                        "target_fats": g.target_fats_g,
                        "target_water": g.target_water_ml,
                    }
                    for g in goals
                ],
            }
            json_bytes = json.dumps(data_dict, indent=2).encode("utf-8")
            return StreamingResponse(
                iter([json_bytes]),
                media_type="application/json",
                headers={"Content-Disposition": 'attachment; filename="nutrimind_export.json"'},
            )

        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            if profile:
                writer.writerow(["Profile", "date_of_birth", str(profile.date_of_birth or "")])
                writer.writerow(["Profile", "biological_sex", str(profile.biological_sex or "")])
                writer.writerow(["Profile", "height_cm", str(profile.height_cm or "")])
                writer.writerow(["Profile", "weight_kg", str(profile.weight_kg or "")])
            for bw in body_weights:
                writer.writerow(["BodyWeight", str(bw.logged_date), f"{float(bw.weight_kg)} kg"])
            for nl in nutrition_logs:
                writer.writerow(["FoodLog", f"{nl.logged_date} {nl.meal_type}", f"{nl.food_name} - {nl.calories_kcal} kcal"])
            for t in tasks:
                due_str = f" - Due: {t.due_date}" if t.due_date else ""
                writer.writerow(["Task", t.status.value if t.status else "pending", f"{t.title}{due_str}"])
            csv_bytes = output.getvalue().encode("utf-8-sig")
            return StreamingResponse(
                iter([csv_bytes]),
                media_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="nutrimind_export.csv"'},
            )

        elif format == "xlsx":
            wb = Workbook()
            ws = wb.active
            ws.title = "NutriMind Data"
            ws.append(["Section", "Key", "Value"])
            if profile:
                ws.append(["Profile", "date_of_birth", str(profile.date_of_birth or "")])
                ws.append(["Profile", "biological_sex", str(profile.biological_sex or "")])
                ws.append(["Profile", "height_cm", str(profile.height_cm or "")])
                ws.append(["Profile", "weight_kg", str(profile.weight_kg or "")])
            for bw in body_weights:
                ws.append(["BodyWeight", str(bw.logged_date), f"{float(bw.weight_kg)} kg"])
            for nl in nutrition_logs:
                ws.append(["FoodLog", f"{nl.logged_date} {nl.meal_type}", f"{nl.food_name} - {nl.calories_kcal} kcal"])
            for t in tasks:
                due_str = f" - Due: {t.due_date}" if t.due_date else ""
                ws.append(["Task", t.status.value if t.status else "pending", f"{t.title}{due_str}"])
            xlsx_bytes = io.BytesIO()
            wb.save(xlsx_bytes)
            xlsx_bytes.seek(0)
            return StreamingResponse(
                iter([xlsx_bytes.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": 'attachment; filename="nutrimind_export.xlsx"'},
            )

        elif format == "pdf":
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph("NutriMind Data Export", styles["Title"]))
            elements.append(Spacer(1, 0.25 * inch))
            if profile:
                elements.append(Paragraph("Profile", styles["Heading2"]))
                data_rows = [
                    ["Date of Birth", str(profile.date_of_birth or "")],
                    ["Biological Sex", str(profile.biological_sex or "")],
                    ["Height (cm)", str(profile.height_cm or "")],
                    ["Weight (kg)", str(profile.weight_kg or "")],
                ]
                table = Table(data_rows, colWidths=[1.5 * inch, 3 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.11, 0.47, 0.70)),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.25 * inch))
            if body_weights:
                elements.append(Paragraph("Body Weights", styles["Heading2"]))
                data_rows = [["Date", "Weight (kg)"]] + [
                    [str(bw.logged_date), str(float(bw.weight_kg))] for bw in body_weights
                ]
                table = Table(data_rows, colWidths=[2 * inch, 2 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.11, 0.47, 0.70)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.25 * inch))
            if nutrition_logs:
                elements.append(Paragraph("Nutrition Logs", styles["Heading2"]))
                data_rows = [["Date", "Food", "Calories"]] + [
                    [str(nl.logged_date), nl.food_name, str(nl.calories_kcal)] for nl in nutrition_logs
                ]
                table = Table(data_rows, colWidths=[1.2 * inch, 2.5 * inch, 1 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.11, 0.47, 0.70)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.25 * inch))
            if tasks:
                elements.append(Paragraph("Tasks", styles["Heading2"]))
                data_rows = [["Status", "Title"]] + [
                    [t.status.value if t.status else "pending", t.title] for t in tasks
                ]
                table = Table(data_rows, colWidths=[1.5 * inch, 3.5 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.11, 0.47, 0.70)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
            doc.build(elements)
            pdf_bytes = buf.getvalue()
            return StreamingResponse(
                iter([pdf_bytes]),
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="nutrimind_export.pdf"'},
            )

        elif format == "txt":
            txt_lines = []
            txt_lines.append("=" * 60)
            txt_lines.append("NutriMind Data Export")
            txt_lines.append("=" * 60)
            if profile:
                txt_lines.append(f"\n--- Profile ---")
                txt_lines.append(f"  Date of Birth:  {profile.date_of_birth or 'N/A'}")
                txt_lines.append(f"  Biological Sex: {profile.biological_sex or 'N/A'}")
                txt_lines.append(f"  Height (cm):    {profile.height_cm or 'N/A'}")
                txt_lines.append(f"  Weight (kg):    {profile.weight_kg or 'N/A'}")
            if body_weights:
                txt_lines.append(f"\n--- Body Weights ---")
                for bw in body_weights:
                    txt_lines.append(f"  {bw.logged_date}: {float(bw.weight_kg)} kg")
            if nutrition_logs:
                txt_lines.append(f"\n--- Nutrition Logs ---")
                for nl in nutrition_logs:
                    txt_lines.append(f"  {nl.logged_date} {nl.meal_type}: {nl.food_name} ({nl.calories_kcal} kcal)")
            if tasks:
                txt_lines.append(f"\n--- Tasks ---")
                for t in tasks:
                    due = f" (due: {t.due_date})" if t.due_date else ""
                    txt_lines.append(f"  [{t.status.value if t.status else 'pending'}] {t.title}{due}")
            txt_lines.append("\n" + "=" * 60)
            txt_bytes = "\n".join(txt_lines).encode("utf-8")
            return StreamingResponse(
                iter([txt_bytes]),
                media_type="text/plain",
                headers={"Content-Disposition": 'attachment; filename="nutrimind_export.txt"'},
            )

    except Exception as exc:
        logger.exception("Data export failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": f"Data export failed: {str(exc)}"},
        )


@router.post("/import")
async def import_data(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    filename = (file.filename or "").lower()
    if not any(filename.endswith(ext) for ext in (".json", ".csv", ".txt")):
        return JSONResponse(status_code=400, content={"success": False, "message": "Only JSON, CSV, or TXT files are supported for import."})

    imported_counts = {"profile": 0, "body_weights": 0, "nutrition_logs": 0, "tasks": 0, "goals": 0}
    skipped_counts = {"body_weights": 0, "nutrition_logs": 0, "tasks": 0, "goals": 0}
    error_details = []

    try:
        content = await file.read()
        text = content.decode("utf-8-sig").strip()

        if filename.endswith(".json"):
            data = json.loads(text)
        elif filename.endswith(".csv") or filename.endswith(".txt"):
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            reader = csv.reader(lines)
            rows = list(reader)

            if not rows:
                data = {"body_weights": [], "nutrition_logs": [], "tasks": [], "profile": None}
            else:
                # Detect format: scan data rows for section keywords
                is_structured = any(
                    len(r) >= 3 and any(s in (r[0] or "").lower() for s in ("profile", "bodyweight", "foodlog", "task"))
                    for r in rows
                )

                if is_structured:
                    data = {"body_weights": [], "nutrition_logs": [], "tasks": [], "profile": None}
                    for row in rows:
                        if len(row) < 3:
                            continue
                        section, field, value = row[0], row[1], row[2]
                        if section == "Profile":
                            if data["profile"] is None:
                                data["profile"] = {}
                            data["profile"][field.lower().replace(" ", "_")] = value
                        elif section == "BodyWeight":
                            data["body_weights"].append({"logged_date": field, "weight_kg": value.replace(" kg", "")})
                        elif section == "FoodLog":
                            parts = value.split(" - ")
                            data["nutrition_logs"].append({"logged_date": field, "food_name": parts[0], "calories_kcal": parts[1].replace(" kcal", "") if len(parts) > 1 else "0"})
                        elif section == "Task":
                            status_val = field
                            title = value
                            due = ""
                            if " - Due: " in value:
                                parts2 = value.split(" - Due: ")
                                title = parts2[0]
                                due = parts2[1]
                            data["tasks"].append({"title": title, "status": status_val, "due_date": due or None})
                else:
                    # Simple CSV: first row may be a header; if it looks like header text, skip it
                    data = {"body_weights": [], "nutrition_logs": [], "tasks": [], "profile": None}
                    start_idx = 0
                    if first_row and first_row[0].lower() in ("title", "status", "date", "section", "type"):
                        start_idx = 1
                    for row in rows[start_idx:]:
                        if len(row) < 2:
                            continue
                        first, second = row[0].strip(), row[1].strip()
                        # Try body weight: first col is a date (YYYY-MM-DD)
                        if len(first) == 10 and first[4] == "-" and first[7] == "-":
                            try:
                                datetime.strptime(first, "%Y-%m-%d")
                                data["body_weights"].append({"logged_date": first, "weight_kg": second.replace(" kg", "")})
                                continue
                            except ValueError:
                                pass
                        # Fallback: treat as task (status, title)
                        data["tasks"].append({"title": second, "status": first, "due_date": row[2].strip() if len(row) > 2 else None})
        else:
            return JSONResponse(status_code=400, content={"success": False, "message": f"Unsupported file format: {filename}"})

        # 1. Profile (upsert: update existing or create)
        if data.get("profile"):
            pdata = data["profile"]
            stmt = select(NutritionProfile).where(NutritionProfile.user_id == current_user.id)
            result = await session.execute(stmt)
            profile = result.scalars().one_or_none()

            if not profile:
                profile = NutritionProfile(user_id=current_user.id)
                session.add(profile)

            if pdata.get("date_of_birth"):
                try:
                    profile.date_of_birth = datetime.strptime(str(pdata["date_of_birth"]), "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    error_details.append({"field": "date_of_birth", "value": str(pdata.get("date_of_birth")), "reason": "Invalid date format"})
            if pdata.get("biological_sex"):
                profile.biological_sex = str(pdata["biological_sex"])
            if pdata.get("height_cm"):
                try:
                    profile.height_cm = float(pdata["height_cm"])
                except (ValueError, TypeError):
                    error_details.append({"field": "height_cm", "value": str(pdata.get("height_cm")), "reason": "Invalid number"})
            if pdata.get("weight_kg"):
                try:
                    profile.weight_kg = float(pdata["weight_kg"])
                except (ValueError, TypeError):
                    error_details.append({"field": "weight_kg", "value": str(pdata.get("weight_kg")), "reason": "Invalid number"})
            imported_counts["profile"] = 1

        # 2. Body Weights (upsert: skip if already exists for that date, update weight)
        for bw in data.get("body_weights", []):
            try:
                date_str = str(bw.get("logged_date", "")).split(" ")[0]
                if not date_str:
                    continue
                logged_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                stmt = select(BodyWeight).where(BodyWeight.user_id == current_user.id, BodyWeight.logged_date == logged_date)
                existing = (await session.execute(stmt)).scalars().one_or_none()
                weight_val = float(bw.get("weight_kg", 0))
                if existing:
                    existing.weight_kg = weight_val
                    skipped_counts["body_weights"] += 1
                else:
                    session.add(BodyWeight(
                        user_id=current_user.id,
                        entry_id=uuid_lib.uuid4(),
                        logged_date=logged_date,
                        weight_kg=weight_val
                    ))
                    imported_counts["body_weights"] += 1
            except Exception as e:
                error_details.append({"type": "body_weight", "data": bw, "reason": str(e)})

        # 3. Nutrition Logs (deduplicate by date, meal_type, food_name, calories)
        for nl in data.get("nutrition_logs", []):
            try:
                raw_date = str(nl.get("logged_date", ""))
                parts = raw_date.split(" ")
                date_str = parts[0]
                meal_type = parts[1] if len(parts) > 1 else "snack"

                # Check for existing log with same date, meal_type, food_name, calories
                stmt = select(NutritionLog).where(
                    NutritionLog.user_id == current_user.id,
                    NutritionLog.logged_date == datetime.strptime(date_str, "%Y-%m-%d").date(),
                    NutritionLog.meal_type == meal_type,
                    NutritionLog.food_name == str(nl.get("food_name", "Imported Food")),
                    NutritionLog.calories_kcal == float(nl.get("calories_kcal", 0))
                )
                existing = (await session.execute(stmt)).scalars().first()
                if existing:
                    skipped_counts["nutrition_logs"] += 1
                else:
                    new_nl = NutritionLog(
                        user_id=current_user.id,
                        entry_id=uuid_lib.uuid4(),
                        logged_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                        meal_type=meal_type,
                        food_name=str(nl.get("food_name", "Imported Food")),
                        serving_description="Imported",
                        calories_kcal=float(nl.get("calories_kcal", 0)),
                        protein_g=0,
                        carbohydrate_g=0,
                        fat_g=0
                    )
                    session.add(new_nl)
                    imported_counts["nutrition_logs"] += 1
            except Exception as e:
                error_details.append({"type": "nutrition_log", "data": nl, "reason": str(e)})

        # 4. Tasks (deduplicate by title + due_date)
        for t in data.get("tasks", []):
            try:
                due_date_str = t.get("due_date", t.get("due", None))
                raw_status = str(t.get("status", "pending"))
                t_status = raw_status if raw_status in ("pending", "completed") else "pending"
                raw_due = str(due_date_str) if due_date_str else None
                t_due = None
                if raw_due:
                    try:
                        t_due = datetime.strptime(raw_due, "%Y-%m-%d %H:%M:%S%z")
                    except ValueError:
                        try:
                            t_due = datetime.strptime(raw_due, "%Y-%m-%d")
                        except ValueError:
                            pass
                
                title = (str(t.get("title", "Imported Task")) or "Imported Task").strip() or "Imported Task"

                # Resolve completed_at: preserve imported value if present;
                # if status is "completed" but no completed_at provided, set to now.
                raw_completed = t.get("completed_at") or t.get("completedAt") or t.get("completion_date")
                t_completed_at: datetime | None = None
                if raw_completed:
                    try:
                        t_completed_at = datetime.fromisoformat(str(raw_completed))
                    except (ValueError, TypeError):
                        try:
                            t_completed_at = datetime.strptime(str(raw_completed), "%Y-%m-%dT%H:%M:%SZ")
                        except (ValueError, TypeError):
                            pass
                if t_status == "completed" and t_completed_at is None:
                    t_completed_at = datetime.now(UTC)

                # Check for existing task with same title and due_date
                stmt = select(Task).where(Task.user_id == current_user.id, Task.title == title)
                if t_due:
                    stmt = stmt.where(Task.due_date == t_due)
                else:
                    stmt = stmt.where(Task.due_date == None)
                existing = (await session.execute(stmt)).scalars().first()
                if existing:
                    skipped_counts["tasks"] += 1
                else:
                    new_task = Task(
                        user_id=current_user.id,
                        task_id=uuid_lib.uuid4(),
                        title=title,
                        priority=TaskPriority(str(t.get("priority", "medium"))),
                        status=t_status,
                        due_date=t_due,
                        completed_at=t_completed_at,
                    )
                    session.add(new_task)
                    imported_counts["tasks"] += 1
            except Exception as e:
                error_details.append({"type": "task", "data": t, "reason": str(e)})

        # 5. Goals
        for g in data.get("goals", []):
            try:
                g_title = str(g.get("title", "")).strip()
                if not g_title:
                    continue
                
                # Check for existing goal with same title
                stmt = select(Goal).where(Goal.user_id == current_user.id, Goal.title == g_title)
                existing = (await session.execute(stmt)).scalars().first()
                if existing:
                    skipped_counts["goals"] += 1
                else:
                    def parse_date(d_str: str | None) -> date | None:
                        if not d_str: return None
                        try: return datetime.strptime(str(d_str), "%Y-%m-%d").date()
                        except: return None
                        
                    new_goal = Goal(
                        user_id=current_user.id,
                        title=g_title,
                        goal_type=GoalType(str(g.get("goal_type", "weight_loss"))),
                        description=g.get("description"),
                        start_date=parse_date(g.get("start_date")),
                        end_date=parse_date(g.get("end_date")),
                        weekly_target=Decimal(str(g.get("weekly_target"))) if g.get("weekly_target") is not None else None,
                        target_calories=int(g.get("target_calories")) if g.get("target_calories") is not None else None,
                        target_protein_g=int(g.get("target_protein")) if g.get("target_protein") is not None else None,
                        target_carbs_g=int(g.get("target_carbs")) if g.get("target_carbs") is not None else None,
                        target_fats_g=int(g.get("target_fats")) if g.get("target_fats") is not None else None,
                        target_water_ml=int(g.get("target_water")) if g.get("target_water") is not None else None,
                    )
                    session.add(new_goal)
                    imported_counts["goals"] += 1
            except Exception as e:
                error_details.append({"type": "goal", "data": g, "reason": str(e)})

        await session.commit()

        msg = f"Imported {imported_counts['profile']} profile, {imported_counts['body_weights']} weights, {imported_counts['nutrition_logs']} logs, {imported_counts['tasks']} tasks, and {imported_counts['goals']} goals."
        if any(v > 0 for v in skipped_counts.values()):
            msg += f" Skipped {skipped_counts['body_weights']} duplicate weights, {skipped_counts['nutrition_logs']} duplicate logs, {skipped_counts['tasks']} duplicate tasks, and {skipped_counts['goals']} duplicate goals."
        
        return {
            "success": True, 
            "message": msg, 
            "imported": imported_counts,
            "skipped": skipped_counts,
            "errors": error_details
        }

    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"success": False, "message": "Invalid JSON format."})
    except Exception as exc:
        await session.rollback()
        logger.exception("Data import failed")
        return JSONResponse(status_code=500, content={"success": False, "message": f"Import failed: {str(exc)}"})

