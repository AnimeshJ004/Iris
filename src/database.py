import os
import datetime
import uuid
import mysql.connector
from mysql.connector import Error as MySQLError
try:
    from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
except ImportError:
    from src.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

# Database connection pool
_pool = None


def _get_connection():
    """Get a MySQL connection, creating the database and tables if needed."""
    global _pool
    if _pool is False:
        return None
    try:
        if _pool is None:
            # Set pool size: serverless environments (Vercel) should use a pool size of 1
            # to avoid exhausting MySQL connection limits as instances scale horizontally.
            is_serverless = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
            pool_size = 1 if is_serverless else 5

            try:
                # Create a connection pool
                _pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="iris_pool",
                    pool_size=pool_size,
                    host=MYSQL_HOST,
                    port=MYSQL_PORT,
                    user=MYSQL_USER,
                    password=MYSQL_PASSWORD,
                    database=MYSQL_DATABASE,
                    connection_timeout=2,
                )
            except MySQLError as err:
                if err.errno == 1049: # Unknown database
                    init_conn = mysql.connector.connect(
                        host=MYSQL_HOST,
                        port=MYSQL_PORT,
                        user=MYSQL_USER,
                        password=MYSQL_PASSWORD,
                        connection_timeout=2,
                    )
                    cursor = init_conn.cursor()
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`")
                    cursor.close()
                    init_conn.close()
                    
                    _pool = mysql.connector.pooling.MySQLConnectionPool(
                        pool_name="iris_pool",
                        pool_size=pool_size,
                        host=MYSQL_HOST,
                        port=MYSQL_PORT,
                        user=MYSQL_USER,
                        password=MYSQL_PASSWORD,
                        database=MYSQL_DATABASE,
                        connection_timeout=2,
                    )
                else:
                    raise

            # Create tables
            _init_tables()

        return _pool.get_connection()

    except MySQLError as e:
        print(f"[Iris] Warning: MySQL connection failed: {e}")
        print("[Iris] Running without database — conversations won't be persisted.")
        _pool = False
        return None


def _init_tables():
    """Create the required tables if they don't exist."""
    conn = _pool.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(36) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL DEFAULT 'New Chat',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_session_id (session_id),
            INDEX idx_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(36),
            user_command TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id),
            INDEX idx_timestamp (timestamp),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ── Session Management ──────────────────────────────────────────────

def create_session(title="New Chat"):
    """Create a new conversation session and return its ID."""
    conn = _get_connection()
    if conn is None:
        return str(uuid.uuid4())

    try:
        session_id = str(uuid.uuid4())
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, title) VALUES (%s, %s)",
            (session_id, title)
        )
        conn.commit()
        cursor.close()
        return session_id
    except MySQLError as e:
        print(f"[Iris] Error creating session: {e}")
        return str(uuid.uuid4())
    finally:
        conn.close()


def get_sessions():
    """Retrieve all conversation sessions, most recent first."""
    conn = _get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT session_id, title, created_at, updated_at "
            "FROM sessions ORDER BY updated_at DESC"
        )
        sessions = cursor.fetchall()
        cursor.close()

        # Convert datetime objects to ISO strings for JSON serialization
        for s in sessions:
            if s.get("created_at"):
                s["created_at"] = s["created_at"].isoformat()
            if s.get("updated_at"):
                s["updated_at"] = s["updated_at"].isoformat()

        return sessions
    except MySQLError as e:
        print(f"[Iris] Error fetching sessions: {e}")
        return []
    finally:
        conn.close()


def update_session_title(session_id, title):
    """Update the title of a session."""
    conn = _get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET title = %s WHERE session_id = %s",
            (title, session_id)
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
    except MySQLError as e:
        print(f"[Iris] Error updating session: {e}")
        return False
    finally:
        conn.close()


def delete_session(session_id):
    """Delete a session and all its conversations (cascaded by FK)."""
    conn = _get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        # Conversations are auto-deleted via ON DELETE CASCADE
        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        conn.commit()
        cursor.close()
        return True
    except MySQLError as e:
        print(f"[Iris] Error deleting session: {e}")
        return False
    finally:
        conn.close()


# ── Conversation Management ─────────────────────────────────────────

def save_conversation(user_command, assistant_response, session_id=None):
    """Save a conversation exchange to the database."""
    conn = _get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (session_id, user_command, assistant_response) "
            "VALUES (%s, %s, %s)",
            (session_id, user_command, assistant_response)
        )

        # Update session's updated_at timestamp
        if session_id:
            cursor.execute(
                "UPDATE sessions SET updated_at = NOW() WHERE session_id = %s",
                (session_id,)
            )

        conn.commit()
        cursor.close()
    except MySQLError as e:
        print(f"[Iris] Error saving conversation: {e}")
    finally:
        conn.close()


def get_conversations(session_id=None, limit=50):
    """Retrieve conversation history, optionally filtered by session."""
    conn = _get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor(dictionary=True)

        if session_id:
            cursor.execute(
                "SELECT session_id, user_command, assistant_response, timestamp "
                "FROM conversations WHERE session_id = %s "
                "ORDER BY timestamp ASC LIMIT %s",
                (session_id, limit)
            )
        else:
            cursor.execute(
                "SELECT session_id, user_command, assistant_response, timestamp "
                "FROM conversations ORDER BY timestamp ASC LIMIT %s",
                (limit,)
            )

        conversations = cursor.fetchall()
        cursor.close()

        # Convert datetime to ISO string
        for c in conversations:
            if c.get("timestamp"):
                c["timestamp"] = c["timestamp"].isoformat()

        return conversations
    except MySQLError as e:
        print(f"[Iris] Error fetching conversations: {e}")
        return []
    finally:
        conn.close()


def clear_conversations(session_id=None):
    """Clear conversation history, optionally for a specific session."""
    conn = _get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        if session_id:
            cursor.execute(
                "DELETE FROM conversations WHERE session_id = %s",
                (session_id,)
            )
        else:
            cursor.execute("DELETE FROM conversations")

        conn.commit()
        cursor.close()
        return True
    except MySQLError as e:
        print(f"[Iris] Error clearing conversations: {e}")
        return False
    finally:
        conn.close()
