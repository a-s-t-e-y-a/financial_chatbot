import sqlite3

DB_FILE = "chatbot.db"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    # Create a table for chat sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Create a table for messages, linked to a session
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
        )
    """)
    conn.commit()
    conn.close()

def create_new_session():
    """Creates a new chat session in the database and returns its ID."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_sessions DEFAULT VALUES")
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    """Retrieves all chat session IDs from the database."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chat_sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    return [s[0] for s in sessions]

def add_message_to_session(session_id, role, content):
    """Adds a message to a specific session in the database."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def get_messages_for_session(session_id):
    """Retrieves all messages for a given session ID from the database."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )
    messages = cursor.fetchall()
    conn.close()
    # Return a list of dictionaries, e.g., [{'role': 'user', 'content': 'Hello'}]
    return [{"role": role, "content": content} for role, content in messages]

def delete_session(session_id):
    """Deletes a chat session and all its messages from the database."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    # First delete all messages for this session
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    
    # Then delete the session itself
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    
    conn.commit()
    conn.close()