import sqlite3, hashlib

def get_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    """)
    conn.commit()
    return conn

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_login(user, pw):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (user,))
    row = c.fetchone(); conn.close()
    return bool(row and row[0] == hash_password(pw))

def create_user(user, pw):
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  (user, hash_password(pw)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_password(user, new_pw):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET password_hash=? WHERE username=?",
              (hash_password(new_pw), user))
    conn.commit(); conn.close()
