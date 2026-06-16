import sqlite3
import json

DB_NAME = "chat.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id TEXT PRIMARY KEY,
            data TEXT
        )
    """)

    conn.commit()
    conn.close()


# ✅ Serialize messages safely
def serialize_messages(messages):
    serialized = []

    for msg in messages:
        if isinstance(msg, dict):
            serialized.append(msg)
        else:
            serialized.append({
                "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                "content": msg.content
            })

    return serialized


# ✅ Save BOTH messages + history
def save_messages(chat_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    messages = serialize_messages(data.get("messages", []))

    safe_data = {
        "messages": messages,
        "history": data.get("history", [])
    }

    cursor.execute("""
        INSERT OR REPLACE INTO sessions (chat_id, data)
        VALUES (?, ?)
    """, (chat_id, json.dumps(safe_data)))

    conn.commit()
    conn.close()


# ✅ Load BOTH messages + history
def load_messages(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM sessions WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return json.loads(row[0])

    return {
        "messages": [],
        "history": []
    }