import sqlite3

def init_db():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            型番          TEXT PRIMARY KEY,
            pmax_stc      REAL,
            voc_stc       REAL,
            vmpp_noc      REAL,
            isc_noc       REAL,
            temp_coeff    REAL
        )
    """)
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
