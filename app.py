import os
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-attendance-tracker-2026")

DATABASE = os.path.join(app.instance_path, "attendance.db")

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SUBJECT_COLORS = [
    "#4f46e5", "#0ea5e9", "#16a34a", "#dc2626", "#f59e0b",
    "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#64748b",
]

# Default college schedule data from Annamacharya Institute of Technology & Sciences
# Department of CSD - Class Time Table (2026-27 Odd Semester, Room A409)
DEFAULT_SUBJECTS = [
    ("Discrete Mathematics & Graph Theory (23ABS9913)", "DMGT", "#4f46e5"),
    ("Universal Human Values (23AHM9905)", "UHV", "#0ea5e9"),
    ("Introduction to Data Science (23APC3201)", "IDS", "#16a34a"),
    ("Advanced Data Structures and Algorithm Analysis (23APC0504)", "ADSA", "#dc2626"),
    ("Object Oriented Programming Through Java (23APC0506)", "JAVA", "#f59e0b"),
    ("Data Science Using Python / IDS Lab (23APC3202)", "IDS LAB", "#8b5cf6"),
    ("OOP Java Lab (23APC0507)", "JAVA LAB", "#ec4899"),
    ("Python Programming (23ASC0501)", "PP", "#14b8a6"),
    ("Environmental Science (23AMC9901)", "EVS", "#f97316"),
    ("Counselling", "COUNS", "#64748b"),
]

# (day_of_week 0=Mon..5=Sat, period_number, subject_short_name, start_time, end_time)
DEFAULT_TIMETABLE_ENTRIES = [
    # MON
    (0, 1, "DMGT", "09:30", "10:20"),
    (0, 2, "DMGT", "10:20", "11:10"),
    (0, 3, "IDS LAB", "11:10", "12:00"),
    (0, 4, "IDS LAB", "12:00", "12:50"),
    (0, 5, "DMGT", "13:50", "14:40"),
    (0, 6, "JAVA", "14:40", "15:30"),
    (0, 7, "UHV", "15:30", "16:20"),
    # TUE
    (1, 1, "ADSA", "09:30", "10:20"),
    (1, 2, "JAVA", "10:20", "11:10"),
    (1, 3, "IDS", "11:10", "12:00"),
    (1, 4, "ADSA", "12:00", "12:50"),
    (1, 5, "PP", "13:50", "14:40"),
    (1, 6, "IDS", "14:40", "15:30"),
    (1, 7, "COUNS", "15:30", "16:20"),
    # WED
    (2, 1, "JAVA", "09:30", "10:20"),
    (2, 2, "IDS", "10:20", "11:10"),
    (2, 3, "IDS", "11:10", "12:00"),
    (2, 4, "JAVA", "12:00", "12:50"),
    (2, 5, "JAVA LAB", "13:50", "14:40"),
    (2, 6, "JAVA LAB", "14:40", "15:30"),
    (2, 7, "DMGT", "15:30", "16:20"),
    # THU
    (3, 1, "PP", "09:30", "10:20"),
    (3, 2, "JAVA", "10:20", "11:10"),
    (3, 3, "EVS", "11:10", "12:00"),
    (3, 4, "ADSA", "12:00", "12:50"),
    (3, 5, "ADSA", "13:50", "14:40"),
    (3, 6, "UHV", "14:40", "15:30"),
    (3, 7, "EVS", "15:30", "16:20"),
    # FRI
    (4, 1, "JAVA", "09:30", "10:20"),
    (4, 2, "IDS", "10:20", "11:10"),
    (4, 3, "DMGT", "11:10", "12:00"),
    (4, 4, "IDS", "12:00", "12:50"),
    (4, 5, "ADSA", "13:50", "14:40"),
    (4, 6, "UHV", "14:40", "15:30"),
    (4, 7, "UHV", "15:30", "16:20"),
    # SAT
    (5, 1, "PP", "09:30", "10:20"),
    (5, 2, "JAVA", "10:20", "11:10"),
    (5, 3, "ADSA", "11:10", "12:00"),
    (5, 4, "DMGT", "12:00", "12:50"),
    (5, 5, "IDS LAB", "13:50", "14:40"),
    (5, 6, "IDS LAB", "14:40", "15:30"),
    (5, 7, "IDS LAB", "15:30", "16:20"),
]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        os.makedirs(app.instance_path, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


def seed_default_for_user(user_id, db):
    """Seed subjects and timetable for a user."""
    # 1. Insert subjects
    subj_map = {}
    for name, short_name, color in DEFAULT_SUBJECTS:
        try:
            db.execute(
                "INSERT INTO subjects (user_id, name, short_name, color) VALUES (?, ?, ?, ?)",
                (user_id, name, short_name, color),
            )
        except sqlite3.IntegrityError:
            pass
        row = db.execute(
            "SELECT id FROM subjects WHERE user_id = ? AND short_name = ?",
            (user_id, short_name),
        ).fetchone()
        if row:
            subj_map[short_name] = row["id"]

    # 2. Insert timetable
    db.execute("DELETE FROM timetable WHERE user_id = ?", (user_id,))
    for day, period, short_name, start_t, end_t in DEFAULT_TIMETABLE_ENTRIES:
        if short_name in subj_map:
            db.execute(
                "INSERT OR REPLACE INTO timetable (user_id, day_of_week, period_number, subject_id, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, day, period, subj_map[short_name], start_t, end_t),
            )
    db.commit()


@app.before_request
def ensure_db():
    db = get_db()
    table_check = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    if not table_check:
        init_db()

    # Create default demo student account if none exists
    user_count = db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if user_count == 0:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("student", generate_password_hash("password123")),
        )
        db.commit()
        demo_user = db.execute("SELECT id FROM users WHERE username = 'student'").fetchone()
        if demo_user:
            seed_default_for_user(demo_user["id"], db)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Template helpers & filters
# ---------------------------------------------------------------------------

@app.context_processor
def inject_helpers():
    return {"DAY_NAMES": DAY_NAMES}


@app.template_filter("time12")
def time12_filter(t_str):
    """Convert HH:MM to 12-hour format e.g. 09:30 -> 9:30 AM, 13:50 -> 1:50 PM."""
    if not t_str:
        return ""
    try:
        dt = datetime.strptime(t_str, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return t_str


# ---------------------------------------------------------------------------
# Routes – Auth
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = None

        if not username:
            error = "Username is required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif not password:
            error = "Password is required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."

        if error is None:
            db = get_db()
            try:
                cursor = db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                new_user_id = cursor.lastrowid
                # Automatically seed timetable from college timetable
                seed_default_for_user(new_user_id, db)
            except sqlite3.IntegrityError:
                error = f"Username '{username}' is already taken."
            else:
                flash("Account created with your CSD Class Timetable! Please log in.", "success")
                return redirect(url_for("login"))

        flash(error, "danger")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome, {user['username']}!", "success")
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes – Subjects
# ---------------------------------------------------------------------------

@app.route("/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        short_name = request.form.get("short_name", "").strip().upper()
        color = request.form.get("color", "#4f46e5")

        if not name or not short_name:
            flash("Subject name and short name are required.", "danger")
        else:
            try:
                db.execute(
                    "INSERT INTO subjects (user_id, name, short_name, color) VALUES (?, ?, ?, ?)",
                    (user_id, name, short_name, color),
                )
                db.commit()
                flash(f"Subject '{name}' ({short_name}) added!", "success")
            except sqlite3.IntegrityError:
                flash(f"Subject '{name}' already exists.", "danger")

        return redirect(url_for("subjects"))

    user_subjects = db.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()

    return render_template("subjects.html", subjects=user_subjects, colors=SUBJECT_COLORS)


@app.route("/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    db = get_db()
    db.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id, session["user_id"]))
    db.commit()
    flash("Subject deleted.", "info")
    return redirect(url_for("subjects"))


# ---------------------------------------------------------------------------
# Routes – Timetable (View and Update anytime)
# ---------------------------------------------------------------------------

@app.route("/timetable", methods=["GET", "POST"])
@login_required
def timetable():
    db = get_db()
    user_id = session["user_id"]

    user_subjects = db.execute(
        "SELECT * FROM subjects WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()

    if not user_subjects:
        flash("Please add your subjects first, or load the default timetable below!", "warning")

    if request.method == "POST":
        # Clear existing timetable for this user
        db.execute("DELETE FROM timetable WHERE user_id = ?", (user_id,))

        for day in range(7):
            prefix = f"day{day}_period"
            # Collect periods from form
            p_nums = set()
            for k in request.form:
                if k.startswith(prefix) and k.endswith("_subject"):
                    num_str = k[len(prefix):-len("_subject")]
                    if num_str.isdigit():
                        p_nums.add(int(num_str))

            for new_period_idx, orig_p_num in enumerate(sorted(p_nums), start=1):
                subj_id = request.form.get(f"day{day}_period{orig_p_num}_subject")
                start_time = request.form.get(f"day{day}_period{orig_p_num}_start", "").strip()
                end_time = request.form.get(f"day{day}_period{orig_p_num}_end", "").strip()

                if subj_id and start_time and end_time:
                    db.execute(
                        "INSERT INTO timetable (user_id, day_of_week, period_number, subject_id, start_time, end_time) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, day, new_period_idx, int(subj_id), start_time, end_time),
                    )

        db.commit()
        flash("Timetable updated successfully! You can change it anytime.", "success")
        return redirect(url_for("timetable"))

    # Load existing timetable
    tt_rows = db.execute(
        "SELECT t.*, s.name AS subject_name, s.short_name, s.color "
        "FROM timetable t JOIN subjects s ON t.subject_id = s.id "
        "WHERE t.user_id = ? ORDER BY t.day_of_week, t.period_number",
        (user_id,),
    ).fetchall()

    timetable_data = {}
    for row in tt_rows:
        day = row["day_of_week"]
        if day not in timetable_data:
            timetable_data[day] = []
        timetable_data[day].append(dict(row))

    return render_template(
        "timetable.html",
        subjects=user_subjects,
        timetable=timetable_data,
    )


@app.route("/timetable/reset-default", methods=["POST"])
@login_required
def reset_default_timetable():
    """Reset to the official CSD Section-1 timetable from PDF."""
    db = get_db()
    seed_default_for_user(session["user_id"], db)
    flash("Loaded official Annamacharya CSD Section-1 timetable!", "success")
    return redirect(url_for("timetable"))


# ---------------------------------------------------------------------------
# Routes – Dashboard (Period-wise Attendance)
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user_id = session["user_id"]

    # Support selecting any date (default is today)
    date_arg = request.args.get("date")
    if date_arg:
        try:
            view_date = datetime.strptime(date_arg, "%Y-%m-%d").date()
        except ValueError:
            view_date = date.today()
    else:
        view_date = date.today()

    today = date.today()
    day_of_week = view_date.weekday()  # 0=Monday

    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    # Get periods for the selected day from user's timetable
    today_periods = db.execute(
        "SELECT t.*, s.name AS subject_name, s.short_name, s.color "
        "FROM timetable t JOIN subjects s ON t.subject_id = s.id "
        "WHERE t.user_id = ? AND t.day_of_week = ? ORDER BY t.period_number",
        (user_id, day_of_week),
    ).fetchall()

    # Get attendance for the viewed date
    attendance_records = db.execute(
        "SELECT * FROM attendance WHERE user_id = ? AND date = ?",
        (user_id, view_date.isoformat()),
    ).fetchall()
    att_map = {a["period_number"]: a["status"] for a in attendance_records}

    periods = []
    for p in today_periods:
        periods.append({
            **dict(p),
            "attendance_status": att_map.get(p["period_number"]),
        })

    # Subject-wise attendance stats for the current month
    month_start = today.replace(day=1)
    subject_stats = db.execute(
        "SELECT s.id, s.name, s.short_name, s.color, "
        "  COUNT(CASE WHEN a.status = 'present' THEN 1 END) AS present_count, "
        "  COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS absent_count, "
        "  COUNT(a.id) AS total "
        "FROM subjects s "
        "LEFT JOIN attendance a ON a.subject_id = s.id AND a.user_id = s.user_id "
        "  AND a.date >= ? "
        "WHERE s.user_id = ? "
        "GROUP BY s.id ORDER BY s.name",
        (month_start.isoformat(), user_id),
    ).fetchall()

    # Overall stats for current month
    overall = db.execute(
        "SELECT "
        "  COUNT(CASE WHEN status = 'present' THEN 1 END) AS present, "
        "  COUNT(CASE WHEN status = 'absent' THEN 1 END) AS absent, "
        "  COUNT(*) AS total "
        "FROM attendance WHERE user_id = ? AND date >= ?",
        (user_id, month_start.isoformat()),
    ).fetchone()

    # Recent 7 days attendance summary
    week_start = view_date - timedelta(days=6)
    recent_days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_att = db.execute(
            "SELECT a.period_number, a.status, s.short_name, s.color "
            "FROM attendance a JOIN subjects s ON a.subject_id = s.id "
            "WHERE a.user_id = ? AND a.date = ? ORDER BY a.period_number",
            (user_id, d.isoformat()),
        ).fetchall()
        recent_days.append({
            "date": d,
            "day_name": DAY_NAMES[d.weekday()],
            "is_today": d == today,
            "is_selected": d == view_date,
            "records": [dict(r) for r in day_att],
        })

    has_timetable = db.execute(
        "SELECT COUNT(*) AS c FROM timetable WHERE user_id = ?", (user_id,)
    ).fetchone()["c"] > 0

    # Chart data
    chart_subjects = []
    for s in subject_stats:
        pct = round(s["present_count"] * 100.0 / s["total"], 1) if s["total"] > 0 else 0
        chart_subjects.append({
            "short_name": s["short_name"],
            "name": s["name"],
            "pct": pct,
            "present": s["present_count"],
            "absent": s["absent_count"],
            "total": s["total"],
            "color": s["color"],
        })

    donut_data = {
        "present": overall["present"] or 0,
        "absent": overall["absent"] or 0,
        "total": overall["total"] or 0,
        "pct": round((overall["present"] or 0) * 100.0 / overall["total"], 1) if overall and overall["total"] else 0,
    }

    trend_data = {
        "labels": [f"{d['day_name'][:3]} {d['date'].strftime('%d/%m')}" for d in recent_days],
        "present": [sum(1 for r in d["records"] if r["status"] == "present") for d in recent_days],
        "absent": [sum(1 for r in d["records"] if r["status"] == "absent") for d in recent_days],
    }

    return render_template(
        "dashboard.html",
        view_date=view_date,
        is_today=(view_date == today),
        today=today,
        prev_date=prev_date,
        next_date=next_date,
        day_name=DAY_NAMES[day_of_week],
        periods=periods,
        subject_stats=[dict(s) for s in subject_stats],
        overall=overall,
        recent_days=recent_days,
        chart_subjects=chart_subjects,
        donut_data=donut_data,
        trend_data=trend_data,
        month_label=today.strftime("%B %Y"),
        has_timetable=has_timetable,
    )


@app.route("/mark", methods=["POST"])
@login_required
def mark_attendance():
    db = get_db()
    user_id = session["user_id"]
    mark_date = request.form.get("date", date.today().isoformat())

    period_keys = [k for k in request.form if k.startswith("period_")]
    marked_count = 0
    for key in period_keys:
        parts = key.split("_")  # period_1_subject_3
        period_num = int(parts[1])
        subject_id = int(parts[3])
        status = request.form.get(key)

        if status in ("present", "absent"):
            try:
                db.execute(
                    "INSERT INTO attendance (user_id, date, period_number, subject_id, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, mark_date, period_num, subject_id, status),
                )
            except sqlite3.IntegrityError:
                db.execute(
                    "UPDATE attendance SET status = ?, marked_at = CURRENT_TIMESTAMP "
                    "WHERE user_id = ? AND date = ? AND period_number = ?",
                    (status, user_id, mark_date, period_num),
                )
            marked_count += 1

    db.commit()
    flash(f"Saved attendance for {marked_count} period(s) on {mark_date}!", "success")
    return redirect(url_for("dashboard", date=mark_date))


@app.route("/mark-all", methods=["POST"])
@login_required
def mark_all():
    """Mark all periods for the viewed day as present or absent."""
    db = get_db()
    user_id = session["user_id"]
    mark_date_str = request.form.get("date", date.today().isoformat())
    try:
        mark_date = datetime.strptime(mark_date_str, "%Y-%m-%d").date()
    except ValueError:
        mark_date = date.today()

    status = request.form.get("status")
    day_of_week = mark_date.weekday()

    if status not in ("present", "absent"):
        flash("Invalid status.", "danger")
        return redirect(url_for("dashboard", date=mark_date.isoformat()))

    periods = db.execute(
        "SELECT period_number, subject_id FROM timetable "
        "WHERE user_id = ? AND day_of_week = ? ORDER BY period_number",
        (user_id, day_of_week),
    ).fetchall()

    for p in periods:
        try:
            db.execute(
                "INSERT INTO attendance (user_id, date, period_number, subject_id, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, mark_date.isoformat(), p["period_number"], p["subject_id"], status),
            )
        except sqlite3.IntegrityError:
            db.execute(
                "UPDATE attendance SET status = ?, marked_at = CURRENT_TIMESTAMP "
                "WHERE user_id = ? AND date = ? AND period_number = ?",
                (status, user_id, mark_date.isoformat(), p["period_number"]),
            )

    db.commit()
    flash(f"All {len(periods)} periods marked as {status.upper()} for {mark_date}!", "success")
    return redirect(url_for("dashboard", date=mark_date.isoformat()))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
