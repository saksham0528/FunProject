# Smart Attendance Management System

A beginner-friendly attendance app built with Python, Streamlit, MongoDB Atlas,
and pandas.

## Requirements

- Python 3.10 or newer
- A MongoDB Atlas cluster and a database user

## Run locally

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and replace the example `MONGO_URI` with the
   connection string from MongoDB Atlas. Ensure your client IP is allowed in
   Atlas Network Access.

4. Start the app:

   ```powershell
   streamlit run app.py
   ```

The app creates the `attendance_db` database and its `students` and `attendance`
collections on first use. It also creates a unique index for student roll
numbers and a unique student/date index so resubmitting a session updates
attendance instead of creating duplicate records.

## Use the app

- **Add Student:** Enter a unique roll number, student name, and class.
- **Mark Attendance:** Choose a date, uncheck students who are absent, and save
  the class session. Resubmitting the same date updates the existing records.
- **Reports:** Review each student's attendance percentage, see the percentage
  chart, and identify students below 75%.

Attendance percentage is calculated as the number of recorded present sessions
divided by the number of distinct dates with attendance records for the class.
Students are not flagged as defaulters until at least one session is recorded.

Do not commit `.env` or share your MongoDB connection string.
