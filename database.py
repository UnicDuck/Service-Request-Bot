import sqlite3
from datetime import datetime


DB_NAME = "requests.db"


def init_db():
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                task TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()
    
def get_user_requests(user_id):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, task, status, created_at
            FROM requests
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (user_id,),
        )

        return cursor.fetchall()


def create_request(user_id, username, full_name, task):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO requests (
                user_id,
                username,
                full_name,
                task,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                full_name,
                task,
                "new",
                created_at,
            ),
        )

        connection.commit()

        return cursor.lastrowid
    
def update_request_status(request_id, status):
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE requests
            SET status = ?
            WHERE id = ?
            """,
            (status, request_id),
        )

        connection.commit()