"""MongoDB data access for the attendance application."""

import os
from datetime import date
from functools import lru_cache

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

load_dotenv()


@lru_cache(maxsize=1)
def get_database() -> Database:
    """Connect to MongoDB and prepare the collections used by the app."""
    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        raise RuntimeError(
            "MONGO_URI is not set. Add your MongoDB connection string to .env."
        )

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        retryWrites=True,
        appname="smart-attendance",
    )
    try:
        client.admin.command("ping")
        database = client["attendance_db"]
        database.students.create_index("roll_no", unique=True)
        database.attendance.create_index(
            [("student_id", ASCENDING), ("date", ASCENDING)],
            unique=True,
        )
    except PyMongoError:
        client.close()
        raise

    return database


def _students() -> Collection:
    return get_database().students


def _attendance() -> Collection:
    return get_database().attendance


def add_student(roll_no: str, name: str, class_name: str) -> ObjectId:
    """Insert a student and return the new MongoDB ID."""
    student = {
        "roll_no": roll_no.strip(),
        "name": name.strip(),
        "class": class_name.strip(),
    }
    if not all(student.values()):
        raise ValueError("Roll number, name, and class are required.")

    return _students().insert_one(student).inserted_id


def get_all_students() -> list[dict]:
    """Return all students ordered by roll number."""
    return list(_students().find().sort("roll_no", ASCENDING))


def mark_attendance(student_id: ObjectId | str, attendance_date: date | str, status: str) -> None:
    """Save or update one student's attendance for a date."""
    try:
        object_id = student_id if isinstance(student_id, ObjectId) else ObjectId(student_id)
    except (InvalidId, TypeError) as exc:
        raise ValueError("The selected student ID is invalid.") from exc

    if isinstance(attendance_date, date):
        date_value = attendance_date.isoformat()
    else:
        try:
            date_value = date.fromisoformat(attendance_date).isoformat()
        except (TypeError, ValueError) as exc:
            raise ValueError("Attendance date must use YYYY-MM-DD format.") from exc

    normalized_status = status.strip().lower()
    if normalized_status not in {"present", "absent"}:
        raise ValueError("Attendance status must be present or absent.")
    if _students().find_one({"_id": object_id}, {"_id": 1}) is None:
        raise ValueError("The selected student no longer exists.")

    _attendance().update_one(
        {"student_id": object_id, "date": date_value},
        {"$set": {"status": normalized_status}},
        upsert=True,
    )


def get_attendance_records() -> list[dict]:
    """Return all attendance records ordered by date."""
    return list(_attendance().find().sort("date", ASCENDING))
