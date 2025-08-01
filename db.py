import sqlite3

def init_db():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()

    # 1) Create table with the new メーカー名 column
    c.execute("""
    CREATE TABLE IF NOT EXISTS modules (
      メーカー名 TEXT,
      型番         TEXT PRIMARY KEY,
      pmax_stc     REAL,
      voc_stc      REAL,
      vmpp_noc     REAL,
      isc_noc      REAL,
      temp_coeff   REAL
    )
    """)
    conn.commit()

    # 2) (Optional) Migration: add columns if you’re upgrading an existing DB
    c.execute("PRAGMA table_info(modules)")
    existing = {row[1] for row in c.fetchall()}
    for col_def in [
      ("メーカー名", "TEXT"),
      ("型番",         "TEXT"),
      ("pmax_stc",     "REAL"),
      ("voc_stc",      "REAL"),
      ("vmpp_noc",     "REAL"),
      ("isc_noc",      "REAL"),
      ("temp_coeff",   "REAL")
    ]:
        col, typ = col_def
        if col not in existing:
            c.execute(f"ALTER TABLE modules ADD COLUMN {col} {typ}")
    conn.commit()
    conn.close()

def save_module(メーカー名, model_number, pmax, voc, vmpp, isc, temp_coeff):
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
      INSERT OR REPLACE INTO modules
        (メーカー名, 型番, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (メーカー名, model_number, pmax, voc, vmpp, isc, temp_coeff))
    conn.commit()
    conn.close()

def load_modules():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
      SELECT メーカー名, 型番, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff
      FROM modules
    """)
    rows = c.fetchall()
    conn.close()
    # return dict keyed by 型番
    return {
      row[1]: {
        "メーカー名": row[0],
        "pmax":         row[2],
        "voc":          row[3],
        "vmpp":         row[4],
        "isc":          row[5],
        "temp_coeff":   row[6],
      }
      for row in rows
    }
