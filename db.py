import hashlib
import psycopg2

from config import DB_DSN
from models import Bid


def init(db=DB_DSN) -> None:
    conn = psycopg2.connect(**db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_systems (
            name TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            version TEXT DEFAULT '',
            owner TEXT DEFAULT ''
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            login TEXT PRIMARY KEY,
            username TEXT,
            password TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            system TEXT DEFAULT ''
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, stored_hash: str) -> bool:
    return hash_password(password) == stored_hash

def auth(login: str, psw: str, db=DB_DSN) -> dict:
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE login=%s;",(login,))
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

def add_user(login: str, psw: str, username="", is_admin=False, db=DB_DSN) -> str:
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute("""
           INSERT INTO users (login, username, password, is_admin)
           VALUES (%s, %s, %s, %s);
        """,(login, username, hash_password(psw), is_admin))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        err = str(e)
        print(f"Error. Can't create user {login}: {err}")
        if "unique" in err:
            return f"User **{login}** already exists!"
        return err
    return ""

def change_user(login: str, system="", username=None, db=DB_DSN) -> bool:
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET system=%s WHERE login=%s;", (system, login))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't change user {login}: {err}")
        return False
    return True

def systems(db=DB_DSN) -> list[str]:
    """List of bidding systems"""
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM all_systems ORDER BY name;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't fetch systems: {err}")
        return []
    return [row[0] for row in rows]

def create_system(name: str, title="", descr="", ver="", author="", db=DB_DSN) -> bool:
    """Create new bidding system"""
    if not name or name in systems(db): return False
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{name}" (
                bid INTEGER DEFAULT 0,
                seq TEXT DEFAULT '',
                description TEXT DEFAULT '',
                pc_min INTEGER DEFAULT 0,
                pc_max INTEGER DEFAULT 37,
                balanced BOOLEAN DEFAULT FALSE,
                suits TEXT DEFAULT ',,,'
            );
        """)
        cursor.execute("""
            INSERT INTO all_systems (name, title, description, version, owner) 
            VALUES (%s, %s, %s, %s, %s);
        """,(name, title, descr, ver, author))
        for bid in range(6):
            cursor.execute(f'INSERT INTO "{name}" (bid) VALUES (%s);', (bid,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't create system '{name}': {err}")
        return False
    return True

def update_system(name: str, title="", descr="", ver="", db=DB_DSN) -> bool:
    """Update system info"""
    if not name: return False
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE all_systems SET title=%s, description=%s, version=%s 
            WHERE name=%s;
        """,(title, descr, ver, name))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't update system '{name}': {err}")
        return False
    return True

def get_system_info(name: str, db=DB_DSN) -> dict | None:
    """Get system info"""
    if not name: return None
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM all_systems WHERE name=%s;", (name,))
        res = cursor.fetchone()
        if res is not None and res[4]:
            cursor.execute("SELECT username FROM users WHERE login=%s;", (res[4],))
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

def delete_system(name: str, db=DB_DSN) -> bool:
    """Delete system"""
    if not name: return False
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM all_systems WHERE name=%s;", (name, ))
        cursor.execute(f'DROP TABLE IF EXISTS "{name}";')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't delete system '{name}': {err}")
        return False
    return True

def clone_system(name: str, new_name: str, author="", db=DB_DSN) -> bool:
    """Clone system"""
    if not name or not new_name: return False
    sys_info = get_system_info(name, db)
    if not sys_info: return False
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute(f'CREATE TABLE "{new_name}" AS SELECT * FROM "{name}";')
        cursor.execute("""
            INSERT INTO all_systems (name, title, description, version, owner) 
            VALUES (%s, %s, %s, %s, %s);
        """,(new_name, sys_info["title"] + " *(copy)*", sys_info["description"], sys_info["version"], author))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't clone system '{name}': {err}")
        return False
    return True

def get_bids(system_name: str, seq: str ="", db=DB_DSN) -> list[Bid]:
    """Returns all consequence of sequence seq"""
    if not system_name: return []
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM "{system_name}" WHERE seq LIKE %s ORDER BY bid;', (seq+"%",))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't fetch sequence '{seq}' from '{system_name}': {err}")
        return []
    if rows is None: return []
    return [Bid(*r) for r in rows]

def upsert_bid(system_name: str, bid: Bid, db=DB_DSN) -> bool:
    """Update/insert bid"""
    if not system_name: return False
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT bid FROM "{system_name}"
            WHERE bid=%s AND seq=%s;
        """, (bid.bid, bid.seq))
        res = cursor.fetchone()
        if res is None:
            cursor.execute(f"""
                INSERT INTO "{system_name}" (bid, seq, description, pc_min, pc_max, balanced, suits)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, bid.to_tuple)
        else:
            cursor.execute(f"""
                UPDATE "{system_name}" 
                SET description=%s, pc_min=%s, pc_max=%s, balanced=%s, suits=%s 
                WHERE bid=%s AND seq=%s;
            """, (bid.description, bid.pc_min, bid.pc_max, bid.balanced, bid.suits, bid.bid, bid.seq))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't update/insert bid {bid.seq_str} into '{system_name}': {err}")
        return False
    return True

def del_thread(system_name: str, bid: Bid, db=DB_DSN) -> int:
    """Delete sequence seq with all answers"""
    if not system_name or not bid: return 0
    del1 = del2 = 0
    try:
        conn = psycopg2.connect(**db)
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM "{system_name}" WHERE seq LIKE %s;', (bid.full_seq + "%",))
        del1 = cursor.rowcount
        cursor.execute(f'DELETE FROM "{system_name}" WHERE seq=%s AND bid=%s;', (bid.seq, bid.bid))
        del2 = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error. Can't delete thread '{bid}' from '{system_name}': {err}")
    return del1 + del2

# def fetch_bid(system_name: str, full_seq: str, db=DB_DSN) -> Bid | None:
#     """Fetch one bid"""
#     if not system_name or not full_seq: return None
#     seq, bid = decomp_seq(full_seq)
#     try:
#         conn = psycopg2.connect(**db)
#         cursor = conn.cursor()
#         cursor.execute(f"""
#             SELECT * FROM "{system_name}"
#             WHERE bid=%s AND seq=%s;
#         """,(bid, seq))
#         res = cursor.fetchone()
#         cursor.close()
#         conn.close()
#     except Exception as err:
#         print(f"Error. Can't fetch bid '{full_seq}' from '{system_name}': {err}")
#         return None
#     if res is None: return None
#     return Bid(*res)

# def fetch_answers(system_name: str, seq: str ="", db=DB_DSN) -> list[Bid] | None:
#     """Fetch all answers to sequence seq"""
#     if not system_name: return None
#     try:
#         conn = psycopg2.connect(**db)
#         cursor = conn.cursor()
#         cursor.execute(f"""
#             SELECT * FROM "{system_name}"
#             WHERE seq=%s
#             ORDER BY bid;
#         """,(seq,))
#         rows = cursor.fetchall()
#         cursor.close()
#         conn.close()
#     except Exception as err:
#         print(f"Error. Can't fetch system '{system_name}': {err}")
#         return []
#     if rows is None: return []
#     bids = [Bid(*row) for row in rows]
#     if len(bids) > 1 and bids[0].bid < 0 and bids[1].bid == 0:
#         bid = bids.pop(0)
#         bids.insert(1, bid)
#     return bids

# def build_tree(system_name: str, seq: str="", opps=False, db=DB_DSN) -> list[Bid]:
#     """Returns full tree of answers to sequence seq"""
#     if not system_name: return []
#     dop = "" if opps else ".0"
#     try:
#         conn = psycopg2.connect(**db)
#         cursor = conn.cursor()
#         cursor.execute(f'SELECT * FROM "{system_name}" WHERE seq LIKE %s ORDER BY bid;', (seq+"%",))
#         rows = cursor.fetchall()
#         cursor.close()
#         conn.close()
#     except Exception as err:
#         print(f"Error. Can't fetch thread '{seq}' from '{system_name}': {err}")
#         return []
#     if rows is None: return []
#     bids = [Bid(*r) for r in rows if opps or r[0] > 0 or not r[1]]
#     # if not opps:
#     #     bids = [b for b in bids if b.bid > 0 or not b.seq]
#     tree = [b for b in bids if b.seq == seq]
#     bids = [b for b in bids if b not in tree]
#     if not bids: return tree
#
#     def build_children(bid: Bid, seq: str):
#         for b in bids:
#             if b.seq == seq and (b.bid > 0 or opps):
#                 bid.children.append(b)
#                 build_children(b, b.full_seq + dop)
#
#     for bid in tree:
#         build_children(bid, bid.full_seq + dop)
#     # tree = fetch_answers(system_name, seq, db)
#     # if not opps and seq:
#     #     while tree and tree[0].bid <= 0:
#     #         tree.pop(0)
#     # for bid in tree:
#     #     bid.children = build_tree(system_name, bid.full_seq + dop, opps, db)
#     return tree

# def next_answer(system_name: str, seq: str="", opps=False, db=DB_DSN) -> int:
#     """Next answer"""
#     if not system_name: return 0
#     bids = [b.bid for b in fetch_answers(system_name, seq if opps or not seq else seq + ".0", db)]
#     if bids:
#         if opps:
#             if not (0 in bids) and can_pass(seq): return 0
#             if not (-1 in bids) and can_contra(seq): return -1
#             if not (-2 in bids) and can_recontra(seq): return -2
#         if bids[-1] >= 0: return bids[-1] + 1
#     else:
#         if not seq: return 0
#         if fetch_bid(system_name, seq, db) is None: return -3
#         if opps:
#             if can_pass(seq): return 0
#             if can_contra(seq): return -1
#             if can_recontra(seq): return -2
#     return max(seq2list(seq)) + 1
#

# def add_answer(system_name: str, seq: str="", opps=False, db=DB_DSN) -> Bid | None:
#     """Add number next answers to sequence seq"""
#     if not system_name: return None
#     nxt = next_answer(system_name, seq, opps, db)
#     if nxt < -2: return None
#     bids = seq2list(seq)
#     bid = None
#     back = 2 + opps
#     if len(bids) > back:
#         bid = fetch_bid(system_name, list2seq(bids[:-back]), db)
#     if bid is not None:
#         bid.bid = nxt
#         bid.seq = seq
#         bid.description = ""
#     else:
#         bid = Bid(nxt, seq)
#     if not opps and seq:
#         bid.seq += ".0"
#     return bid if upsert_bid(system_name, bid, db) else None
