# database.py

import sqlite3
import config

DB_FILE = 'lumen_data.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for user-specific settings
    # CORRECTED: The DEFAULT value in a CREATE TABLE statement cannot be a parameter.
    # We must format it directly into the string. It's safe as it comes from our config.
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            model TEXT NOT NULL DEFAULT '{config.DEFAULT_MODEL}'
        )
    ''')

    # Table for conversation messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON messages (user_id)')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def get_user_settings(user_id: int) -> dict:
    """
    Retrieves settings for a user.
    If the user doesn't exist, creates them with default settings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT model FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row:
        settings = dict(row)
    else:
        # User not found, create a new entry with defaults
        cursor.execute("INSERT INTO user_settings (user_id, model) VALUES (?, ?)",
                       (user_id, config.DEFAULT_MODEL))
        conn.commit()
        settings = {'model': config.DEFAULT_MODEL}

    conn.close()
    return settings

def update_user_settings(user_id: int, model: str):
    """Updates a user's model setting, creating the user if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Use INSERT OR REPLACE (UPSERT) to handle both new and existing users
    cursor.execute('''
        INSERT INTO user_settings (user_id, model)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET model = excluded.model;
    ''', (user_id, model))
    conn.commit()
    conn.close()

def get_conversation_history(user_id: int) -> list:
    """
    Retrieves the full conversation history for a user,
    prepending the system prompt.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Always start with the system prompt, which is not stored in the DB
    history = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    history.extend([dict(row) for row in rows])
    return history

def add_message_to_history(user_id: int, role: str, content: str):
    """Adds a new message to a user's conversation history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

def clear_conversation_history(user_id: int) -> bool:
    """
    Deletes all messages for a specific user from the history.
    Returns True if any messages were deleted, False otherwise.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_rows > 0