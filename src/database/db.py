"""
SQLite database — patients, doctors, analyses.
Uses Python's built-in sqlite3, zero extra dependencies.
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/clinical.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create all tables and seed default doctor account."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS doctors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            hospital    TEXT NOT NULL,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS patients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      TEXT UNIQUE NOT NULL,
            full_name       TEXT NOT NULL,
            age             INTEGER NOT NULL,
            gender          TEXT NOT NULL,
            phone           TEXT,
            address         TEXT,
            disease_id      TEXT NOT NULL,
            doctor_id       INTEGER NOT NULL,
            registered_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      TEXT NOT NULL,
            disease_id      TEXT NOT NULL,
            risk_level      TEXT NOT NULL,
            risk_score      REAL NOT NULL,
            parameters      TEXT NOT NULL,
            findings        TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            doctor_id       INTEGER NOT NULL,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );
    """)

    # Seed default doctor if not exists
    _seed_doctor(cur, "doctor", "clinical2026", "Dr. Suraj Chopade", "City General Hospital")
    _seed_doctor(cur, "admin",  "admin2026",    "Dr. Admin",         "Admin Hospital")

    conn.commit()
    conn.close()
    print(f"Database initialised at {DB_PATH}")


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _seed_doctor(cur, username, password, full_name, hospital):
    cur.execute(
        "INSERT OR IGNORE INTO doctors (username, password, full_name, hospital) VALUES (?,?,?,?)",
        (username, _hash(password), full_name, hospital)
    )


# ── Doctor auth ───────────────────────────────────────────────────────────────

def verify_doctor(username: str, password: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM doctors WHERE username=? AND password=?",
        (username, _hash(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctor_by_id(doctor_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Patient registration ──────────────────────────────────────────────────────

def register_patient(
    full_name: str, age: int, gender: str,
    phone: str, address: str,
    disease_id: str, doctor_id: int
) -> str:
    """Register a new patient and return their generated patient_id."""
    conn = get_connection()
    # Generate patient ID: PT-YYYYMMDD-XXXX
    date_str = datetime.now().strftime("%Y%m%d")
    count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    patient_id = f"PT-{date_str}-{count+1:04d}"

    conn.execute(
        """INSERT INTO patients
           (patient_id, full_name, age, gender, phone, address, disease_id, doctor_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (patient_id, full_name, age, gender, phone, address, disease_id, doctor_id)
    )
    conn.commit()
    conn.close()
    return patient_id


def get_patients_for_doctor(doctor_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, d.full_name as doctor_name
           FROM patients p
           JOIN doctors d ON p.doctor_id = d.id
           WHERE p.doctor_id = ?
           ORDER BY p.registered_at DESC""",
        (doctor_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patient(patient_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM patients WHERE patient_id=?", (patient_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Analysis storage ──────────────────────────────────────────────────────────

def save_analysis(
    patient_id: str, disease_id: str,
    risk_level: str, risk_score: float,
    parameters: str, findings: str,
    recommendations: str, doctor_id: int
) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO analyses
           (patient_id, disease_id, risk_level, risk_score,
            parameters, findings, recommendations, doctor_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (patient_id, disease_id, risk_level, risk_score,
         parameters, findings, recommendations, doctor_id)
    )
    conn.commit()
    analysis_id = cur.lastrowid
    conn.close()
    return analysis_id


def get_analyses_for_patient(patient_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM analyses WHERE patient_id=? ORDER BY created_at DESC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    