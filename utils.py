TREFF = "♣️"
CARO = "♦️"
COEUR = "♥️"
PIK = "♠️"
SA = "NT"
SUITS = ["NT", "♣️", "♦️", "♥️", "♠️"]
REPLACE = {
    "_c": TREFF,
    "_t": TREFF,
    "_d": CARO,
    "_h": COEUR,
    "_s": PIK,
    "_p": PIK,
    "_т": TREFF,
    "_б": CARO,
    "_ч": COEUR,
    "_п": PIK,
    "_+": COEUR + PIK,
    "_-": TREFF + CARO,
}

def repr_bid(b) -> str:
    bid = int(b)
    if bid == 0: return "-"
    elif bid == -1: return "X"
    elif bid == -2: return "XX"
    return f"{(bid-1)//5+1}{SUITS[bid%5]}"

def decomp_seq(full_seq: str):
    if not full_seq: return None, None
    if "." in full_seq:
        seq, bid = full_seq.rsplit(".", 1)
    else: seq, bid = "", full_seq
    return seq, int(bid)

def seq2list(seq: str) ->list[int]:
    return [int(b) for b in seq.split(".")] if seq else []

def list2seq(lst: list[int]) -> str:
    return ".".join([str(n) for n in lst])

def repl_str(s: str) -> str:
    for k in REPLACE.keys():
        s = s.replace(k, REPLACE[k])
    return s

def can_pass(seq: str) -> bool:
    if not seq: return True
    bids = seq2list(seq)
    if bids[-1]: return True
    if len(bids) < 3: return True
    if bids[-2]: return True
    return False

def can_contra(seq: str) -> bool:
    if not seq: return False
    if seq == "0": return False
    if len(seq) == 1: return True
    bids = seq2list(seq)
    if bids[-1] > 0: return True
    if bids[-1] < 0: return False
    if len(bids) == 2: return False
    if bids[-2] != 0: return False
    if bids[-3] > 0: return True
    return False

def can_recontra(seq: str) -> bool:
    if len(seq) < 4: return False
    bids = seq2list(seq)
    if bids[-1] == -1: return True
    if len(bids) < 4: return False
    if bids[-1] == 0 and bids[-2] == 0 and bids[-3] == -1: return True
    return False