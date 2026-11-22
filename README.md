# 📋 Attendance Tracker

A web-based attendance tracker built with **Flask**, **SQLite**, and **Chart.js** designed for period-wise timetable tracking in college/university classes.

Includes a pre-configured schedule for **Annamacharya Institute of Technology & Sciences (AITS) - Dept of CSD (Section-1, Room A409)**, and allows students to customize or update their timetable anytime.

---

## ✨ Features

- **User Authentication**: Secure user registration, password hashing (Werkzeug), and session-based login.
- **Period-Wise Attendance**:
  - Automatically loads the day's scheduled periods based on your weekly timetable.
  - Mark individual periods as **Present** (✅) or **Absent** (❌).
  - Quick action buttons to mark **All Present** or **All Absent** in one click.
  - Date navigation: jump to previous/next days or pick any date from the calendar to view or update past records.
- **Dynamic Weekly Timetable**:
  - Full weekly college grid overview (Monday to Saturday, Periods 1 to 7, plus lunch break).
  - Add, edit, or delete periods and customize start/end timings anytime.
  - One-click button to reset or load the official CSD Section-1 timetable.
- **Subject Management**:
  - Add custom subjects with short codes and unique color badges.
- **Visual Analytics & Interactive Graphs (Chart.js)**:
  - **Subject-Wise Attendance Bar Chart**: Visualizes attendance percentage for each subject against the 75% requirement.
  - **Overall Ratio Donut Chart**: Clear breakdown of total Present vs. Absent periods.
  - **7-Day Trend Chart**: Daily attendance trends across recent days.
  - Interactive toggle buttons to filter charts.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask, Werkzeug, SQLite3
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla ES6), Chart.js (offline bundled)
- **Database**: SQLite (auto-initialized)

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/gattujayakrishna48-arch/Attendance-tracker.git
cd Attendance-tracker
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

### 4. Open in your browser
Navigate to:
```
http://127.0.0.1:5000
```

> **Default Demo Account:**
> - **Username:** `student`
> - **Password:** `password123`
>
> *(Or click **Sign Up** to create your own account)*

---

## 📁 Project Structure

```
attendance-tracker/
├── app.py                  # Main Flask application and API routes
├── schema.sql              # Database schema (users, subjects, timetable, attendance)
├── requirements.txt        # Python package requirements
├── .gitignore              # Files to ignore in git
├── README.md               # Project documentation
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout with navbar, alerts & scripts
│   ├── login.html          # Sign in page
│   ├── signup.html         # Sign up page
│   ├── dashboard.html      # Main dashboard with periods, stats & charts
│   ├── timetable.html      # Weekly schedule viewer & timetable editor
│   └── subjects.html       # Subject creation & management
└── static/                 # Static assets
    ├── style.css           # Responsive modern styling
    ├── script.js           # Client-side UI logic & Chart.js initializer
    └── chart.umd.min.js    # Chart.js library (bundled locally for offline use)
```

---

## 📜 License
MIT

