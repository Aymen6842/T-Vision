import sqlite3
import hashlib
import json
import os
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = "vision_agent.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Conversations Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Messages Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            image_path TEXT,
            metadata TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES conversations (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class UserManager:
    def create_user(self, username, password):
        conn = get_db_connection()
        try:
            c = conn.cursor()
            pwd_hash = hash_password(password)
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      (username, pwd_hash))
            conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None # Username exists
        finally:
            conn.close()

    def verify_user(self, username, password):
        conn = get_db_connection()
        c = conn.cursor()
        pwd_hash = hash_password(password)
        c.execute('SELECT id, username FROM users WHERE username = ? AND password_hash = ?', 
                  (username, pwd_hash))
        user = c.fetchone()
        conn.close()
        return dict(user) if user else None

class ChatHistoryManager:
    def create_session(self, session_id: str, user_id: int):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)',
                  (session_id, user_id, "New Conversation"))
        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, content: str, 
                   image_path: str = None, metadata: dict = None):
        conn = get_db_connection()
        c = conn.cursor()
        meta_json = json.dumps(metadata) if metadata else None
        c.execute('''
            INSERT INTO messages (session_id, role, content, image_path, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, role, content, image_path, meta_json))
        
        # Update conversation timestamp
        c.execute('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()

    def get_user_sessions(self, user_id: int):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_session_messages(self, session_id: str):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_session(self, session_id: str):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        c.execute('DELETE FROM conversations WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()

# Initialize on import
if not os.path.exists(DB_PATH):
    init_db()
