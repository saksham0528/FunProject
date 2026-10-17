"""Create clearly labeled demo data for locally viewing attendance reports."""

from __future__ import annotations

import random
from datetime import date, timedelta

from pymongo.errors import DuplicateKeyError, PyMongoError

from db import add_student, get_all_students, mark_attendance


DEMO_STUDENTS = [
    ("DEMO101", "Aarav Mehta", "AIDS-2A"),
    ("DEMO102", "Diya Shah", "AIDS-2A"),
    ("DEMO103", "Kabir Nair", "AIDS-2A"),
    ("DEMO104", "Meera Iyer", "AIDS-2A"),
    ("DEMO105", "Vihaan Rao", "AIDS-2A"),
    ("DEMO106", "Anaya Kapoor", "AIDS-2B"),
    ("DEMO107", "Arjun Menon", "AIDS-2B"),
    ("DEMO108", "Sara Khan", "AIDS-2B"),
    ("DEMO109", "Ishaan Das", "AIDS-2B"),
    ("DEMO110", "Tara Joshi", "AIDS-2B"),
]


def session_dates(count: int = 18) -> list[date]:
    """Return weekday dates from the previous several weeks."""
    today = date.today()
    candidates = [today - timedelta(days=offset) for offset in range(1, 45)]
    return sorted(random.sample([item for item in candidates if item.weekday() < 5], count))


def main() -> None:
    random.seed(20261018)
    existing = {student["roll_no"]: student for student in get_all_students()}

    for roll_no, name, class_name in DEMO_STUDENTS:
        if roll_no not in existing:
            try:
                add_student(roll_no, name, class_name)
            except DuplicateKeyError:
                pass

    demo_students = {
        student["roll_no"]: student
        for student in get_all_students()
        if student["roll_no"].startswith("DEMO")
    }
    dates = session_dates()
    records_written = 0
    for student in demo_students.values():
        attendance_rate = random.uniform(0.52, 0.98)
        for attendance_date in dates:
            status = "present" if random.random() < attendance_rate else "absent"
            mark_attendance(student["_id"], attendance_date, status)
            records_written += 1

    print(
        f"Demo data ready: {len(demo_students)} students, "
        f"{len(dates)} sessions, {records_written} attendance records."
    )


if __name__ == "__main__":
    try:
        main()
    except (PyMongoError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Could not seed demo data: {type(exc).__name__}: {exc}") from exc
