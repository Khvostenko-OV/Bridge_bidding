import csv

from config import st
import db
from models import Bid
from utils import can_pass, can_contra, can_recontra, list2seq


def get_bid(bid: int, seq: str) -> Bid | None:
    """Get Bid object from bids"""
    return next((b for b in st.session_state.bids if b.bid == bid and b.seq == seq), None)

def get_answers(seq: str ="") -> list[Bid]:
    res = [b for b in st.session_state.bids if b.seq == seq and (b.bid > 0 or st.session_state.opps or not seq)]
    res.sort(key=lambda b: b.bid)
    if len(res) > 1 and res[0].bid < 0 and res[1].bid == 0:
        bid = res.pop(0)
        res.insert(1, bid)
    return res

def next_answer(bid: Bid = None) -> int:
    """Next answer to bid"""
    seq = "" if bid is None else bid.full_seq + ("" if st.session_state.opps else ".0")
    answers = [b.bid for b in get_answers(seq)]
    if answers:
        if st.session_state.opps:
            if not (0 in answers) and can_pass(seq): return 0
            if not (-1 in answers) and can_contra(seq): return -1
            if not (-2 in answers) and can_recontra(seq): return -2
        if bid is not None:
            answers.append(bid.bid)
        return max(answers) + 1
    return 0 if bid is None else bid.next_bid(st.session_state.opps)

def add_answer(bid: Bid = None) -> bool:
    """Add next answer to bid"""
    nxt = next_answer(bid)
    seq = "" if bid is None else bid.full_seq + ("" if st.session_state.opps else ".0")
    bids = [] if bid is None else bid.seq_list
    back = 2 + st.session_state.opps
    prev_bid = None
    if len(bids) > back:
        prev_bid = get_bid(bids[-back-1], list2seq(bids[:-back-1]))
    if prev_bid is None:
        new_bid = Bid(nxt, seq)
    else:
        new_bid = Bid(**prev_bid.to_dict)
        new_bid.bid = nxt
        new_bid.seq = seq
        new_bid.description = ""
    if db.upsert_bid(st.session_state.curr_system, new_bid):
        st.session_state.bids.append(new_bid)
        return True
    else:
        st.session_state.message = {"type": "E", "message": f"Fail to create bid {new_bid.seq_str}"}
    return False

def save_system() -> bool:
    """Save system to .csv file"""
    if not st.session_state.curr_system: return False
    try:
        with open(f"{st.session_state.curr_system}.csv", "w", encoding="utf-8") as f:
            f.write(st.session_state.sys_info["title"] + "\n")
            f.write(st.session_state.sys_info["description"] + "\n")
            f.write("~~~~~~\n")
            for b in st.session_state.bids:
                b.suits = b.suits.strip() if b.suits else ",,,"
                f.write(f'{b.bid},{b.seq},"{b.description}",{b.pc_min},{b.pc_max},{b.balanced},"{b.suits}"\n')
    except Exception as err:
        print(f"Error. Can't save System '{st.session_state.curr_system}': {err}")
        st.session_state.message = {"type": "E", "message": f"Fail to save System **{st.session_state.curr_system}**: {err}"}
        return False
    st.session_state.message = {"type": "S", "message": f"System **{st.session_state.curr_system}** saved"}
    return True

def load_system(filename):
    """Load system from .csv file"""
    try:
        sys_name = filename.split(".")[0]
        if sys_name in st.session_state.systems: raise Exception(f"System '{sys_name}' already exists")
        if not db.create_system(sys_name, author=st.session_state.user): raise Exception(f"Can't create System '{sys_name}'")
        with open(filename, "r", encoding="utf-8") as f:
            title = f.readline().strip()
            s = f.readline().strip()
            lines =[]
            while s != "~~~~~~":
                lines.append(s)
                s = f.readline().strip()
            description = "\n".join(lines)
            db.update_system(sys_name, title, description)
            reader = csv.reader(f)
            for line in reader:
                db.upsert_bid(sys_name, Bid(int(line[0]),
                                            line[1],
                                            line[2].strip('"'),
                                            int(line[3]),
                                            int(line[4]),
                                            line[5] == "True",
                                            line[6].strip('"')
                                            ))
    except Exception as err:
        print(f"Error. Can't load System '{st.session_state.curr_system}': {err}")
        st.session_state.message = {"type": "E", "message": f"Fail to load System from **{filename}**: {err}"}
        st.session_state.systems = db.systems()
        return False

    st.session_state.curr_system = sys_name
    st.session_state.sys_info = db.get_system_info(sys_name)
    st.session_state.bids = db.get_bids(sys_name)
    st.session_state.systems = db.systems()
    st.session_state.message = {"type": "S", "message": f"System {st.session_state.curr_system} loaded"}
    return True
