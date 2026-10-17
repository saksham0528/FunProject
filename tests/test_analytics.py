import unittest

from analytics import build_attendance_summary


class AttendanceSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.students = [
            {"_id": "student-1", "roll_no": "CS101", "name": "Riya", "class": "AIDS-2A"},
            {"_id": "student-2", "roll_no": "CS102", "name": "Aman", "class": "AIDS-2A"},
        ]

    def test_calculates_percentages_and_includes_students_without_records(self) -> None:
        records = [
            {"student_id": "student-1", "date": "2026-09-25", "status": "present"},
            {"student_id": "student-1", "date": "2026-09-26", "status": "absent"},
        ]

        summary, total_sessions = build_attendance_summary(self.students, records)

        self.assertEqual(total_sessions, 2)
        self.assertEqual(summary["attendance_pct"].tolist(), [50.0, 0.0])
        self.assertEqual(summary["sessions_present"].tolist(), [1, 0])

    def test_returns_zero_percentages_before_first_session(self) -> None:
        summary, total_sessions = build_attendance_summary(self.students, [])

        self.assertEqual(total_sessions, 0)
        self.assertEqual(summary["attendance_pct"].tolist(), [0.0, 0.0])

    def test_returns_empty_summary_when_there_are_no_students(self) -> None:
        summary, total_sessions = build_attendance_summary([], [])

        self.assertTrue(summary.empty)
        self.assertEqual(total_sessions, 0)


if __name__ == "__main__":
    unittest.main()
