import sqlite3

from config import DB_NAME
from models import Bid
from utils import decomp_seq


def init(db_name=DB_NAME) -> None:
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS all_systems (
            name TEXT UNIQUE,
            title TEXT DEFAULT "",
            description TEXT DEFAULT "",
            version TEXT DEFAULT ""
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def systems(db_name=DB_NAME) -> list[str]:
    """List of bidding systems"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name
        FROM all_systems
        ORDER BY name;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def create_system(name: str, title="", descr="", ver="", db_name=DB_NAME) -> bool:
    """Create new bidding system"""
    if not name or name in systems(db_name): return False
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{name}" (
                bid INTEGER DEFAULT 0,
                seq TEXT DEFAULT "",
                description TEXT DEFAULT "",
                pc_min INTEGER DEFAULT 0,
                pc_max INTEGER DEFAULT 37,
                balanced BOOLEAN DEFAULT FALSE,
                suits TEXT DEFAULT ""
            );
        """)
        sql = "INSERT INTO all_systems (name, title, description, version) VALUES (?, ?, ?, ?);"
        cursor.execute(sql, (name, title, descr, ver))
        for bid in range(6):
            cursor.execute(f'INSERT INTO "{name}" (bid) VALUES ({bid});')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't create system '{name}': {err}")
        return False
    return True

def update_system(name: str, title="", descr="", ver="", db_name=DB_NAME) -> bool:
    """Update system info"""
    if not name: return False
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        sql = "UPDATE all_systems SET title=?, description=?, version=? WHERE name=?;"
        cursor.execute(sql, (title, descr, ver, name))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't update system '{name}': {err}")
        return False
    return True

def get_system(name: str, db_name=DB_NAME) -> dict | None:
    """Get system info"""
    if not name: return None
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT * FROM all_systems WHERE name = "{name}";
    """)
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    if res is None: return {}
    return {
        "name": res[0],
        "title": res[1],
        "description": res[2],
        "version": res[3],
    }

def delete_system(name: str, db_name=DB_NAME) -> bool:
    """Delete system"""
    if not name: return False
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM all_systems WHERE name = '{name}';")
        cursor.execute(f"DROP TABLE IF EXISTS '{name}';")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't delete system '{name}': {err}")
        return False
    return True

def fetch_bid(system_name: str, full_seq: str, db_name=DB_NAME) -> Bid | None:
    """Fetch one bid"""
    if not system_name or not full_seq: return None
    seq, bid = decomp_seq(full_seq)
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM "{system_name}"
            WHERE bid={bid} AND seq="{seq}";
        """)
        res = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't fetch bid '{full_seq}' from '{system_name}': {err}")
        return None
    if res is None: return None
    return Bid(*res)

def fetch_answers(system_name: str, seq: str ="", db_name=DB_NAME) -> list[Bid] | None:
    """Fetch all answers to sequence seq"""
    if not system_name: return None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM "{system_name}"
            WHERE seq="{seq}"
            ORDER BY bid;
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't fetch system '{system_name}': {err}")
        return []
    if rows is None: return []
    return [Bid(*row) for row in rows]

def build_tree(system_name: str, seq: str="", db_name=DB_NAME) -> list[Bid] | None:
    """Returns full tree of answers to sequence seq"""
    if not system_name: return None
    tree = fetch_answers(system_name, seq, db_name)
    for bid in tree:
        bid.children = build_tree(system_name, bid.full_seq + ".0", db_name)
    return tree

def update_bid(system_name: str, bid: Bid, db_name=DB_NAME) -> bool:
    """Update/insert bid"""
    if not system_name: return False
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE "{system_name}" 
            SET description="{bid.description}", pc_min={bid.pc_min}, pc_max={bid.pc_max}, balanced={bid.balanced}, suits="{bid.suits}" 
            WHERE bid={bid.bid} AND seq="{bid.seq}";
        """)
        cursor.execute(f"""
            SELECT * FROM "{system_name}"
            WHERE bid={bid.bid} AND seq="{bid.seq}";
        """)
        res = cursor.fetchone()
        if res is None:
            cursor.execute(f"""
                INSERT INTO "{system_name}" (bid, seq, description, pc_min, pc_max, balanced, suits)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, bid.to_tuple)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't update/insert bid {bid.seq_str} into '{system_name}': {err}")
        return False
    return True

def add_answers(system_name: str, seq: str="", number=1, db_name=DB_NAME) -> bool:
    """Add number next answers to sequence seq"""
    if not system_name: return False
    if seq:
        bid = fetch_bid(system_name, seq, db_name)
        if bid is None: return False
        new_seq = seq + ".0"
        start = bid.bid + 1
    else:
        new_seq = ""
        start = 0
    answers = fetch_answers(system_name, new_seq, db_name)
    if answers:
        start = answers[-1].bid + 1
    res = [update_bid(system_name, Bid(start + i, new_seq), db_name) for i in range(number)]
    return all(res)

def del_thread(system_name: str, seq: str, db_name=DB_NAME) -> int:
    """Delete sequence seq with all answers"""
    if not system_name or not seq: return 0
    prev_seq, bid = decomp_seq(seq)
    del1 = del2 = 0
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""DELETE FROM "{system_name}" WHERE seq LIKE '{seq}%';""")
        del1 = cursor.rowcount
        cursor.execute(f"""DELETE FROM "{system_name}" WHERE seq = '{prev_seq}' AND bid = {bid};""")
        del2 = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't delete thread '{seq}' from '{system_name}': {err}")
    return del1 + del2
