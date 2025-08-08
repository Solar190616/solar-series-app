+import sqlite3
+import sys
+from pathlib import Path
+
+sys.path.append(str(Path(__file__).resolve().parents[1]))
+import auth
+
+
+def make_test_db(tmp_path):
+    db_path = tmp_path / "users.db"
+    def _get_db():
+        conn = sqlite3.connect(db_path)
+        c = conn.cursor()
+        c.execute(
+            """
+            CREATE TABLE IF NOT EXISTS users (
+                username TEXT PRIMARY KEY,
+                password_hash TEXT
+            )
+            """
+        )
+        conn.commit()
+        return conn
+    return _get_db
+
+
+def test_update_password_returns_false_for_unknown_user(tmp_path, monkeypatch):
+    monkeypatch.setattr(auth, "get_db", make_test_db(tmp_path))
+    auth.ensure_permanent_credentials()
+    assert auth.update_password("ghost", "pw") is False
+
+
+def test_update_password_updates_existing_user(tmp_path, monkeypatch):
+    monkeypatch.setattr(auth, "get_db", make_test_db(tmp_path))
+    auth.ensure_permanent_credentials()
+    assert auth.create_user("alice", "pw1")
+    assert auth.update_password("alice", "pw2")
+    assert auth.check_login("alice", "pw2")
 
EOF
)
