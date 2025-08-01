# db.py
import sqlite3

# Use a single DB file for both modules and pcs
_conn = sqlite3.connect("modules.db", check_same_thread=False)
_cur  = _conn.cursor()

def init_db():
    # existing modules table
    _cur.execute("""
    CREATE TABLE IF NOT EXISTS modules(
      manufacturer TEXT,
      model_number TEXT PRIMARY KEY,
      pmax_stc REAL,
      voc_stc REAL,
      vmpp_noc REAL,
      isc_noc REAL,
      temp_coeff REAL
    )""")
    # new pcs table
    _cur.execute("""
    CREATE TABLE IF NOT EXISTS pcs(
      name TEXT PRIMARY KEY,
      max_voltage REAL,
      mppt_min_voltage REAL,
      mppt_count INTEGER,
      mppt_max_current REAL
    )""")
    _conn.commit()

def save_module(manufacturer, model_no, pmax, voc, vmpp, isc, tc):
    _cur.execute("""
      INSERT OR REPLACE INTO modules
      (manufacturer, model_number, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (manufacturer, model_no, pmax, voc, vmpp, isc, tc))
    _conn.commit()

def load_modules():
    _cur.execute("SELECT model_number, manufacturer, pmax_stc, voc_stc, vmpp_noc, isc_noc, temp_coeff FROM modules")
    rows = _cur.fetchall()
    return {
        row[0]:{
          "manufacturer": row[1],
          "pmax_stc": row[2],
          "voc_stc": row[3],
          "vmpp_noc": row[4],
          "isc_noc": row[5],
          "temp_coeff": row[6],
        }
        for row in rows
    }

def delete_module(model_no):
    _cur.execute("DELETE FROM modules WHERE model_number=?", (model_no,))
    _conn.commit()

# --- New PCS functions ---
def save_pcs(name, max_v, min_v, count, max_i):
    _cur.execute("""
      INSERT OR REPLACE INTO pcs
      (name, max_voltage, mppt_min_voltage, mppt_count, mppt_max_current)
      VALUES (?, ?, ?, ?, ?)
    """, (name, max_v, min_v, count, max_i))
    _conn.commit()

def load_pcs():
    _cur.execute("SELECT name, max_voltage, mppt_min_voltage, mppt_count, mppt_max_current FROM pcs")
    rows = _cur.fetchall()
    return {
      row[0]: {
        "max_voltage": row[1],
        "mppt_min_voltage": row[2],
        "mppt_count": row[3],
        "mppt_max_current": row[4],
      }
      for row in rows
    }

def delete_pcs(name):
    _cur.execute("DELETE FROM pcs WHERE name=?", (name,))
    _conn.commit()
