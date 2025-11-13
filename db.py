import hashlib
import sqlite3

from config import DB_NAME
from models import Bid
from utils import decomp_seq, can_contra, can_recontra, seq2list, can_pass, list2seq


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
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
            login TEXT UNIQUE,
            username TEXT,
            password TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            system TEXT DEFAULT ""
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash

def auth(login: str, psw: str, db_name=DB_NAME) -> dict:
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM users WHERE login = "{login}";
        """)
        res = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't auth: {err}")
        return {"Error": f"{err}"}
    if res is None:
        return {"Error": f"User **{login}** not found!"}
    if verify_password(psw, res[2]):
        return {
            "login": res[0],
            "username": res[1],
            "is_admin": res[3],
            "system": res[4],
        }
    else:
        return {"Error": f"Wrong pair login/password!"}

def add_user(login: str, psw: str, username="", is_admin=False, db_name=DB_NAME) -> str:
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT INTO users (login, username, password, is_admin)
                       VALUES (?, ?, ?, ?);""",
                       (login, username, hash_password(psw), is_admin))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        err = str(e)
        print(f"Error. Can't create user {login}: {err}")
        if "UNIQUE" in err:
            return f"User **{login}** already exists!"
        return err
    return ""

def change_user(login: str, system="", username=None, db_name=DB_NAME) -> bool:
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE users 
            SET system="{system}"  
            WHERE login="{login}";
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't change user {login}: {err}")
        return False
    return True

def systems(db_name=DB_NAME) -> list[str]:
    """List of bidding systems"""
    try:
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
    except Exception as err:
        print(f"Error. Can't fetch systems: {err}")
        return []
    return [row[0] for row in rows]

def create_system(name: str, title="", descr="", ver="", author="", db_name=DB_NAME) -> bool:
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
                suits TEXT DEFAULT ",,,"
            );
        """)
        cursor.execute("""
            INSERT INTO all_systems (name, title, description, version, owner) 
            VALUES (?, ?, ?, ?, ?);""",
            (name, title, descr, ver, author))
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
        cursor.execute("""
            UPDATE all_systems SET title=?, description=?, version=? 
            WHERE name=?;""",
            (title, descr, ver, name))
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
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM all_systems WHERE name = "{name}";
        """)
        res = cursor.fetchone()
        if not res is None and res[4]:
            cursor.execute(f"""SELECT username FROM users WHERE login = "{res[4]}";""")
            user = cursor.fetchone()
            username = user[0] if user else ""
        else:
            username = ""
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't fetch system '{name}': {err}")
        return None
    if res is None: return None
    return {
        "name": res[0],
        "title": res[1],
        "description": res[2],
        "version": res[3],
        "owner": res[4],
        "owner_name": username,
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

def clone_system(name: str, new_name: str, author="", db_name=DB_NAME) -> bool:
    """Clone system"""
    if not name or not new_name: return False
    sys_info = get_system(name, db_name)
    if not sys_info: return False
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE {new_name} AS SELECT * FROM {name};")
        cursor.execute("""
            INSERT INTO all_systems (name, title, description, version, owner) 
            VALUES (?, ?, ?, ?, ?);""",
    (new_name, sys_info["title"] + " *(copy)*", sys_info["description"], sys_info["version"], author))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't clone system '{name}': {err}")
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
    bids = [Bid(*row) for row in rows]
    if len(bids) > 1 and bids[0].bid < 0 and bids[1].bid == 0:
        bid = bids.pop(0)
        bids.insert(1, bid)
    return bids

def build_tree(system_name: str, seq: str="", opps=False, db_name=DB_NAME) -> list[Bid]:
    """Returns full tree of answers to sequence seq"""
    if not system_name: return []
    dop = "" if opps else ".0"
    tree = fetch_answers(system_name, seq, db_name)
    if not opps and seq:
        while tree and tree[0].bid <= 0:
            tree.pop(0)
    for bid in tree:
        bid.children = build_tree(system_name, bid.full_seq + dop, opps, db_name)
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

def next_answer(system_name: str, seq: str="", opps=False, db_name=DB_NAME) -> int:
    """Next answer"""
    if not system_name: return 0
#    print("Seq: ", seq)
    bids = [b.bid for b in fetch_answers(system_name, seq if opps else seq + ".0", db_name)]
#    print("Answers: ", bids)
    if bids:
        if opps:
            if not (0 in bids) and can_pass(seq): return 0
            if not (-1 in bids) and can_contra(seq): return -1
            if not (-2 in bids) and can_recontra(seq): return -2
        if bids[-1] > 0: return bids[-1] + 1
    else:
        if not seq: return 0
        if fetch_bid(system_name, seq, db_name) is None: return -3
        if opps:
            if can_pass(seq): return 0
            if can_contra(seq): return -1
            if can_recontra(seq): return -2
    return max(seq2list(seq)) + 1


def add_answer(system_name: str, seq: str="", opps=False, db_name=DB_NAME) -> bool:
    """Add number next answers to sequence seq"""
    if not system_name: return False
    nxt = next_answer(system_name, seq, opps, db_name)
    # print("Next answer: ", nxt)
    if nxt < -2: return False
    bids = seq2list(seq)
    bid = None
    back = 2 + opps
    if len(bids) > back:
        bid = fetch_bid(system_name, list2seq(bids[:-back]), db_name)
    if bid is not None:
        bid.bid = nxt
        bid.seq = seq
        bid.description = ""
    else:
        bid = Bid(nxt, seq)
    if not opps:
        bid.seq += ".0"
    return update_bid(system_name, bid, db_name)

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
