 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/auth.py b/auth.py
index 2ee0400c4b4e8e3e243be4e6d0ecb75d7cbb46b6..7950beed9139dd581a63291c5c2e80870a4ea898 100644
--- a/auth.py
+++ b/auth.py
@@ -1,76 +1,123 @@
-import sqlite3, hashlib
+import sqlite3, hashlib, os, hmac
 
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
 
-def hash_password(pw):
-    return hashlib.sha256(pw.encode()).hexdigest()
+def hash_password(pw, salt=None, iterations=100_000):
+    """Create a salted PBKDF2 hash for the given password."""
+    if salt is None:
+        salt = os.urandom(16)
+    elif isinstance(salt, str):
+        salt = bytes.fromhex(salt)
+    pwd_hash = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, iterations)
+    return f"{salt.hex()}${pwd_hash.hex()}"
+
+def verify_password(pw, stored_hash, iterations=100_000):
+    """Verify a password against a stored hash. Supports legacy unsalted hashes."""
+    if '$' in stored_hash:
+        salt_hex, hash_hex = stored_hash.split('$', 1)
+        salt = bytes.fromhex(salt_hex)
+        calc_hash = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, iterations).hex()
+        return hmac.compare_digest(calc_hash, hash_hex)
+    else:
+        # Legacy SHA256 hash without salt
+        legacy = hashlib.sha256(pw.encode()).hexdigest()
+        return hmac.compare_digest(legacy, stored_hash)
 
 def ensure_permanent_credentials():
     """Ensure the permanent smartsolar user exists with correct password"""
     conn = get_db()
     c = conn.cursor()
     
     # Check if smartsolar user exists
     c.execute("SELECT password_hash FROM users WHERE username=?", ('smartsolar',))
     row = c.fetchone()
     
+    correct_pw = 'solar27'
     if row:
-        # Update password if it's different
-        correct_hash = hash_password('solar27')
-        if row[0] != correct_hash:
-            c.execute("UPDATE users SET password_hash=? WHERE username=?", 
-                     (correct_hash, 'smartsolar'))
+        stored_hash = row[0]
+        if verify_password(correct_pw, stored_hash):
+            if '$' not in stored_hash:
+                # Upgrade legacy hash to salted hash
+                c.execute(
+                    "UPDATE users SET password_hash=? WHERE username=?",
+                    (hash_password(correct_pw), 'smartsolar'),
+                )
+                conn.commit()
+        else:
+            c.execute(
+                "UPDATE users SET password_hash=? WHERE username=?",
+                (hash_password(correct_pw), 'smartsolar'),
+            )
             conn.commit()
     else:
         # Create the user if it doesn't exist
-        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
-                  ('smartsolar', hash_password('solar27')))
+        c.execute(
+            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
+            ('smartsolar', hash_password(correct_pw)),
+        )
         conn.commit()
     
     conn.close()
 
 def check_login(user, pw):
     # Ensure permanent credentials are available
     ensure_permanent_credentials()
     
     conn = get_db(); c = conn.cursor()
     c.execute("SELECT password_hash FROM users WHERE username=?", (user,))
-    row = c.fetchone(); conn.close()
-    return bool(row and row[0] == hash_password(pw))
+    row = c.fetchone()
+    if not row:
+        conn.close()
+        return False
+    stored_hash = row[0]
+    if verify_password(pw, stored_hash):
+        if '$' not in stored_hash:
+            # Upgrade legacy hash to salted hash
+            c.execute(
+                "UPDATE users SET password_hash=? WHERE username=?",
+                (hash_password(pw), user),
+            )
+            conn.commit()
+        conn.close()
+        return True
+    conn.close()
+    return False
 
 def create_user(user, pw):
     # Ensure permanent credentials are available
     ensure_permanent_credentials()
     
     conn = get_db(); c = conn.cursor()
     try:
-        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
-                  (user, hash_password(pw)))
+        c.execute(
+            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
+            (user, hash_password(pw)),
+        )
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
 
EOF
)
