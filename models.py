import json

from utils import repr_bid, can_pass, can_contra, can_recontra


class Bid:
    def __init__(self,
                 bid: int,
                 seq: str ="",
                 description: str ="",
                 pc_min: int =0,
                 pc_max: int =37,
                 balanced: bool =False,
                 suits: str =",,,"
                ):
        self.bid = bid
        self.seq = seq
        self.description = description
        self.pc_min = pc_min
        self.pc_max = pc_max
        self.balanced = balanced
        self.suits = suits
        # self.children = []

    def __str__(self):
        return repr_bid(self.bid)

    @property
    def to_dict(self) -> dict:
        return {
            "bid": self.bid,
            "seq": self.seq,
            "description": self.description,
            "pc_min": self.pc_min,
            "pc_max": self.pc_max,
            "balanced": self.balanced,
            "suits": self.suits,
        }

    @property
    def to_json(self) -> str:
        return json.dumps(self.to_dict)

    @property
    def to_tuple(self) -> tuple:
        return self.bid, self.seq, self.description, self.pc_min, self.pc_max, self.balanced, self.suits

    @property
    def to_str(self) -> str:
        return f"**{self.seq_str} :** {self.description}"

    @property
    def full_seq(self) -> str:
        if self.seq:
            return f"{self.seq}.{self.bid}"
        else:
            return str(self.bid)

    @property
    def seq_str(self) -> str:
        #if self.full_seq == "0": return "pass"
        bids = self.full_seq.split(".")
        res = " ".join([repr_bid(bid) for bid in bids])
        return res.replace("-", "pass", 1) if res.startswith("-") else res

    @property
    def seq_list(self) -> list[int]:
        return [ int(b) for b in self.full_seq.split(".")]

    def to_markdown(self, opps=False) -> str:
        if opps:
            bids = self.full_seq.split(".")
            res = ""
            for i, bid in enumerate(bids):
                res += f":red-background[{repr_bid(bid)} ]" if i%2 else f":blue-background[{repr_bid(bid)} ]"
        else:
            res = f":blue-background[{self.seq_str} ]"
        return f"{res} {self.description}"

    def next_bid(self, opps=False) -> int:
        if opps:
            if can_pass(self.full_seq): return 0
            if can_contra(self.full_seq): return -1
            if can_recontra(self.full_seq): return -2
        if self.bid > 0: return self.bid + 1
        return max(self.seq_list) + 1
