"""Pandas transformations for attendance reports."""

import pandas as pd


SUMMARY_COLUMNS = [
    "roll_no",
    "name",
    "class",
    "sessions_present",
    "sessions_total",
    "attendance_pct",
]


def build_attendance_summary(
    students: list[dict], records: list[dict]
) -> tuple[pd.DataFrame, int]:
    """Calculate each student's attendance against all recorded class sessions."""
    total_sessions = len({record["date"] for record in records})
    summary = pd.DataFrame(
        [
            {
                "student_id": str(student["_id"]),
                "roll_no": student["roll_no"],
                "name": student["name"],
                "class": student["class"],
            }
            for student in students
        ]
    )
    if summary.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS), total_sessions

    if total_sessions:
        record_frame = pd.DataFrame(
            [
                {
                    "student_id": str(record["student_id"]),
                    "status": record["status"],
                }
                for record in records
            ]
        )
        present_counts = (
            record_frame.loc[record_frame["status"] == "present"]
            .groupby("student_id")
            .size()
        )
        summary["sessions_present"] = (
            summary["student_id"].map(present_counts).fillna(0).astype(int)
        )
        summary["sessions_total"] = total_sessions
        summary["attendance_pct"] = (
            summary["sessions_present"] / total_sessions * 100
        ).round(1)
    else:
        summary["sessions_present"] = 0
        summary["sessions_total"] = 0
        summary["attendance_pct"] = 0.0

    return summary[SUMMARY_COLUMNS], total_sessions
