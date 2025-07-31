import sqlite3

def init_db():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            name TEXT PRIMARY KEY,
            voc REAL,
            vmp REAL,
            temp_coeff REAL
        )
    """)
    conn.commit()
    conn.close()

def save_module(name, voc, vmp, temp_coeff):
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO modules (name, voc, vmp, temp_coeff)
        VALUES (?, ?, ?, ?)
    """, (name, voc, vmp, temp_coeff))
    conn.commit()
    conn.close()

def load_modules():
    conn = sqlite3.connect("modules.db")
    c = conn.cursor()
    c.execute("SELECT name, voc, vmp, temp_coeff FROM modules")
    rows = c.fetchall()
    conn.close()
    return {name: {"voc": voc, "vmp": vmp, "temp_coeff": temp_coeff} for name, voc, vmp, temp_coeff in rows}
