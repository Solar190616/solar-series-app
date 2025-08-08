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

def ensure_permanent_credentials():
    """Ensure the permanent smartsolar user exists with correct password"""
    conn = get_db()
    c = conn.cursor()
    
    # Check if smartsolar user exists
    c.execute("SELECT password_hash FROM users WHERE username=?", ('smartsolar',))
    row = c.fetchone()
    
    if row:
        # Update password if it's different
        correct_hash = hash_password('solar27')
        if row[0] != correct_hash:
            c.execute("UPDATE users SET password_hash=? WHERE username=?", 
                     (correct_hash, 'smartsolar'))
            conn.commit()
    else:
        # Create the user if it doesn't exist
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  ('smartsolar', hash_password('solar27')))
        conn.commit()
    
    conn.close()

def check_login(user, pw):
    # Ensure permanent credentials are available
    ensure_permanent_credentials()
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username=?", (user,))
    row = c.fetchone(); conn.close()
    return bool(row and row[0] == hash_password(pw))

def create_user(user, pw):
    # Ensure permanent credentials are available
    ensure_permanent_credentials()
    
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
    # Ensure permanent credentials are available
    ensure_permanent_credentials()
    
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET password_hash=? WHERE username=?",
              (hash_password(new_pw), user))
    conn.commit(); conn.close()

# Initialize permanent credentials when module is imported
ensure_permanent_credentials()
