"""
StudyMate AI - storage layer
----------------------------
SQLite database for user accounts, chats and messages.
Passwords are never stored in plain text: each one is hashed with
PBKDF2-HMAC-SHA256 and a random per-user salt.
"""

import os
import re
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.getenv("STUDYMATE_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "studymate.db"))
PBKDF2_ITERATIONS = 200_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                pw_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                material TEXT NOT NULL DEFAULT '',
                material_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS).hex()


# ---- Users ----

def create_user(name: str, email: str, password: str) -> dict:
    """Register a user. Raises ValueError with a user-facing message on bad input."""
    name, email = name.strip(), email.strip().lower()
    if not name:
        raise ValueError("Please enter your name.")
    if not EMAIL_RE.match(email):
        raise ValueError("Please enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    salt = secrets.token_hex(16)
    try:
        with _conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, pw_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, email, _hash(password, salt), salt, _now()),
            )
            return {"id": cur.lastrowid, "name": name, "email": email}
    except sqlite3.IntegrityError:
        raise ValueError("An account with this email already exists. Please log in.")


def authenticate(email: str, password: str):
    """Return the user dict if the credentials are correct, else None."""
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if row and secrets.compare_digest(row["pw_hash"], _hash(password, row["salt"])):
        return {"id": row["id"], "name": row["name"], "email": row["email"]}
    return None


# ---- Chats ----

def create_chat(user_id: int, title: str = "New chat") -> int:
    with _conn() as conn:
        return conn.execute(
            "INSERT INTO chats (user_id, title, created_at) VALUES (?, ?, ?)", (user_id, title, _now())
        ).lastrowid


def list_chats(user_id: int) -> list:
    with _conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, title, material_name FROM chats WHERE user_id = ? ORDER BY id DESC", (user_id,)
        )]


def get_chat(chat_id: int, user_id: int):
    """Only returns the chat if it belongs to this user."""
    with _conn() as conn:
        row = conn.execute("SELECT * FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id)).fetchone()
    return dict(row) if row else None


def rename_chat(chat_id: int, title: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE chats SET title = ? WHERE id = ?", (title[:60], chat_id))


def set_material(chat_id: int, name: str, text: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE chats SET material = ?, material_name = ? WHERE id = ?", (text, name, chat_id))


def delete_chat(chat_id: int, user_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))


# ---- Messages ----

def add_message(chat_id: int, role: str, kind: str, content) -> int:
    """kind is 'text', 'quiz' or 'cards'; non-text content is stored as JSON."""
    payload = content if kind == "text" else json.dumps(content)
    with _conn() as conn:
        return conn.execute(
            "INSERT INTO messages (chat_id, role, kind, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, role, kind, payload, _now()),
        ).lastrowid


def get_messages(chat_id: int) -> list:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)).fetchall()
    out = []
    for r in rows:
        m = dict(r)
        if m["kind"] != "text":
            m["content"] = json.loads(m["content"])
        out.append(m)
    return out
