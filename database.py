"""資料庫連線與 schema 初始化"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "chimei.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema():
    with db_session() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            avatar TEXT,
            gender TEXT,
            stage TEXT NOT NULL,
            dept TEXT,
            month TEXT,
            mentor TEXT,
            overall_progress INTEGER DEFAULT 0,
            team_status TEXT DEFAULT 'green',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stage_benchmarks (
            stage TEXT NOT NULL,
            dimension TEXT NOT NULL,
            score REAL NOT NULL,
            PRIMARY KEY (stage, dimension)
        );

        CREATE TABLE IF NOT EXISTS competencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            dimension TEXT NOT NULL,
            score REAL NOT NULL,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            evaluator TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS ilps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            goal TEXT,
            motivation TEXT,
            strategy TEXT,
            resources TEXT,
            barriers TEXT,
            kpi TEXT,
            timeline TEXT,
            eportfolio_rating INTEGER,
            ai_generated_plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS monthly_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            item TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            total INTEGER NOT NULL,
            month TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS weekly_focus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            title TEXT NOT NULL,
            tag TEXT,
            urgency TEXT DEFAULT 'normal',
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS reflections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            content TEXT NOT NULL,
            ai_feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            tag TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            meta TEXT,
            match_keywords TEXT
        );

        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            method TEXT NOT NULL,
            score REAL,
            feedback TEXT,
            evaluator TEXT,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS coach_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        -- ===== 課程模組 =====
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            type TEXT NOT NULL,
            instructor TEXT,
            location TEXT,
            competency_uplift TEXT,
            duration_minutes INTEGER DEFAULT 60,
            schedule_type TEXT DEFAULT 'on_demand',
            scheduled_at TEXT,
            credit_hours REAL DEFAULT 0,
            cme_credits REAL DEFAULT 0,
            requires_qr_checkin INTEGER DEFAULT 0,
            requires_instructor_signoff INTEGER DEFAULT 0,
            requires_certificate_upload INTEGER DEFAULT 0,
            auto_complete_after_signin INTEGER DEFAULT 0,
            content_url TEXT,
            capacity INTEGER DEFAULT 100,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            status TEXT DEFAULT 'registered',
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            final_score REAL,
            instructor_feedback TEXT,
            certificate_url TEXT,
            self_reflection TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            UNIQUE(employee_id, course_id)
        );

        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL,
            checkin_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            method TEXT,
            ip_address TEXT,
            notes TEXT,
            FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
        );

        CREATE TABLE IF NOT EXISTS qr_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            issued_by TEXT,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used_count INTEGER DEFAULT 0,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );


        CREATE TABLE IF NOT EXISTS reflection_feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reflection_id INTEGER NOT NULL,
            employee_id TEXT NOT NULL,
            instructor TEXT NOT NULL,
            content TEXT NOT NULL,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reflection_id) REFERENCES reflections(id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE INDEX IF NOT EXISTS idx_competencies_emp ON competencies(employee_id);
        CREATE INDEX IF NOT EXISTS idx_ilps_emp ON ilps(employee_id);
        CREATE INDEX IF NOT EXISTS idx_milestones_emp ON milestones(employee_id);
        CREATE INDEX IF NOT EXISTS idx_reflections_emp ON reflections(employee_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_emp ON enrollments(employee_id);
        CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_enrollment ON attendance_logs(enrollment_id);
        """)


if __name__ == "__main__":
    init_schema()
    print(f"Database initialized at: {DB_PATH}")
