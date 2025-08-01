import sqlite3

def init_db():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()

    # 1) Create the table if it doesn't exist (new schema)
    c.execute("""
    CREATE TABLE IF NOT EXISTS modules (
      型番       TEXT PRIMARY KEY,
      pmax_stc   REAL,
      voc_stc    REAL,
      vmpp_noc   REAL,
      isc_noc    REAL,
      temp_coeff REAL
    )
    """)
    conn.commit()

    # 2) Check existing columns
    c.execute("PRAGMA table_info(modules)")
    existing = {row[1] for row in c.fetchall()}   # row[1] is the column name

    # 3) Add any missing columns (no-op if they already exist)
    for col, typ in [
      ("型番", "TEXT"),
      ("pmax_stc", "REAL"),
      ("voc_stc", "REAL"),
      ("vmpp_noc", "REAL"),
      ("isc_noc", "REAL"),
      ("temp_coeff", "REAL")
    ]:
        if col not in existing:
            c.execute(f"ALTER TABLE modules ADD COLUMN {col} {typ}")
    conn.commit()
    conn.close()

def save_module(model_number, pmax, voc, vmpp, isc, temp_coeff):
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO modules
          (型番, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (model_number, pmax, voc, vmpp, isc, temp_coeff))
    conn.commit()
    conn.close()

def load_modules():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
      SELECT 型番, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff
      FROM modules
    """)
    rows = c.fetchall()
    conn.close()
    # return a dict keyed by 型番
    return {
      row[0]: {
        "pmax":       row[1],
        "voc":        row[2],
        "vmpp":       row[3],
        "isc":        row[4],
        "temp_coeff": row[5],
      }
      for row in rows
    }
