import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import db


def setup_module(module):
    db._conn = sqlite3.connect(":memory:", check_same_thread=False)
    db._cur = db._conn.cursor()
    db.init_db()
    db.delete_pcs("マルチパワコン")


def test_default_pcs_setting():
    db.save_pcs("PCS1", "Model1", 400.0, 100.0, 2, 10.0)
    db.save_pcs("PCS2", "Model2", 500.0, 120.0, 3, 12.0, is_default=True)

    pcs = db.load_pcs()

    assert pcs["PCS1"]["is_default"] is False
    assert pcs["PCS2"]["is_default"] is True
    assert sum(1 for p in pcs.values() if p["is_default"]) == 1
 
