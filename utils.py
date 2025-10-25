TREFF = "♣️"
CARO = "♦️"
COEUR = "♥️"
PIK = "♠️"
SA = "NT"
SUITS = ["NT", "♣️", "♦️", "♥️", "♠️"]
REPLACE = {
    "_c": TREFF,
    "_d": CARO,
    "_h": COEUR,
    "_s": PIK,
    "_т": TREFF,
    "_б": CARO,
    "_ч": COEUR,
    "_п": PIK,
    "_+": COEUR + PIK,
    "_-": TREFF + CARO,
}

def repr_bid(bid: int) -> str:
    if bid == 0: return "pass"
    elif bid == -1: return "X"
    elif bid == -2: return "XX"
    return f"{(bid-1)//5+1}{SUITS[bid%5]}"

def decomp_seq(full_seq: str):
    if not full_seq: return None, None
    if "." in full_seq:
        seq, bid = full_seq.rsplit(".", 1)
    else: seq, bid = "", full_seq
    return seq, int(bid)

def repl_str(s: str) -> str:
    for k in REPLACE.keys():
        s = s.replace(k, REPLACE[k])
    return s