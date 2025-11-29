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
    return False
