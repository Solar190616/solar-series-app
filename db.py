import sqlite3

def init_db():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    # Create table if missing (Keeps existing data on redeploy)
    c.execute("""
    CREATE TABLE IF NOT EXISTS modules (
      manufacturer  TEXT,
      model_number  TEXT PRIMARY KEY,
      pmax_stc      REAL,
      voc_stc       REAL,
      vmpp_noc      REAL,
      isc_noc       REAL,
      temp_coeff    REAL
    )
    """)
    conn.commit()
    conn.close()

def save_module(manufacturer, model_number, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff):
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
      INSERT OR REPLACE INTO modules
        (manufacturer, model_number, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (manufacturer, model_number, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff))
    conn.commit()
    conn.close()

def load_modules():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
      SELECT manufacturer, model_number, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff
      FROM modules
    """)
    rows = c.fetchall()
    conn.close()
    modules = {}
    for mfr, mn, pmax, voc, vmpp, isc, tc in rows:
        modules[mn] = {
            "manufacturer": mfr,
            "pmax_stc":     pmax,
            "voc_stc":      voc,
            "vmpp_noc":     vmpp,
            "isc_noc":      isc,
            "temp_coeff":   tc
        }
    return modules
