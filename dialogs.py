from bidding import swap_system
from config import st
import db
from models import Bid
from utils import repl_str


@st.dialog("Welcome", dismissible=False)
def login_dialog():
    login = st.text_input("Login", key="lgn")
    password = st.text_input("Password", type="password", key="psw")
    col1, col2, col3 = st.columns([1, 1, 2])
    if col1.button("Enter") and login and password:
        log = db.auth(login, password)
        if "Error" in log:
            st.error(log["Error"])
        else:
            st.session_state.user = login
            st.session_state.username = log["username"] or login
            st.session_state.is_admin = log["is_admin"]
            swap_system(log["system"])
            st.session_state.show_login = None
            st.rerun()
    if col2.button("Register"):
        st.session_state.show_login = "signup"
        st.rerun()
    if col3.button("Read only"):
        st.session_state.systems = db.systems()
        st.session_state.show_login = None
        st.rerun()

@st.dialog("New user", dismissible=False)
def register_dialog():
    login = st.text_input("Login", key="lgn")
    password = st.text_input("Password", type="password", key="psw")
    username = st.text_input("Username", key="usrnm")
    col1, col2, col3 = st.columns([1, 1, 2])
    if col1.button("Register") and login and password:
        err = db.add_user(login, password, username)
        if err:
            st.error(err)
        else:
            st.session_state.user = login
            st.session_state.username = username
            st.session_state.systems = db.systems()
            st.session_state.show_login = None
            st.rerun()
    if col2.button("Login"):
        st.session_state.show_login = "login"
        st.rerun()
    if col3.button("Read only"):
        st.session_state.systems = db.systems()
        st.session_state.show_login = None
        st.rerun()

@st.dialog("Confirm Deletion", dismissible=False)
def delete_system_dialog():
    if not st.session_state.curr_system: return
    st.warning(f"Are you sure you want to delete System '**{st.session_state.curr_system}**'?")
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Yes 🗑"):
        if db.delete_system(st.session_state.curr_system):
            swap_system()
            st.session_state.message = {"type": "S", "message": f"System **{st.session_state.curr_system}** deleted"}
        else:
            st.session_state.message = {"type": "E", "message": f"Fail to delete **{st.session_state.curr_system}**"}
        st.session_state.edit_system = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.edit_system = None
        st.rerun()

@st.dialog("Clone system", dismissible=False)
def clone_system_dialog():
    if not st.session_state.curr_system: return
    st.subheader(f"Create a copy of '**{st.session_state.curr_system}**'")
    new_name = st.text_input("New short name", key="new_name")
    st.session_state.systems = db.systems()
    if new_name in st.session_state.systems:
        st.error("This name is already in use!")
        new_name = ""
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Yes") and new_name:
        if db.clone_system(st.session_state.curr_system, new_name, st.session_state.user):
            swap_system(new_name)
        else:
            st.session_state.message = {"type": "E", "message": f"Fail to clone **{st.session_state.curr_system}**"}
        st.session_state.edit_system = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.edit_system = None
        st.rerun()


@st.dialog("Edit bid", width="medium", dismissible=False)
def edit_bid_dialog():
    if not st.session_state.curr_system: return
    bid = Bid(**st.session_state.edit_bid.to_dict)
    suits = bid.suits.split(",")
    suits = suits * 4 if suits == [""] else suits
    st.subheader(bid.seq_str)
    bid.description = st.text_input("Description", value=bid.description, key="bid_description")
    col1, col2, col3 = st.columns(3)
    bid.pc_min = col1.number_input("Min PC", value=bid.pc_min, min_value=0, max_value=37, key="min_pc")
    bid.pc_max = col2.number_input("Max PC", value=bid.pc_max, min_value=0, max_value=37, key="max_pc")
    bid.balanced = col3.checkbox("Balanced", value=bid.balanced, key="balanced")
    col_11, col_21, col_31, col_41 = st.columns(4)
    suits[0] = col_11.text_input("♣️", value=suits[0], key="c_min")
    suits[1] = col_21.text_input("♦️", value=suits[1], key="d_min")
    suits[2] = col_31.text_input("♥️", value=suits[2], key="h_min")
    suits[3] = col_41.text_input("♠️", value=suits[3], key="s_min")

    col_save, col_no = st.columns(2)
    if col_save.button("✅ Save"):
        bid.description = repl_str(bid.description)
        bid.suits = ",".join(suits)
        if db.upsert_bid(st.session_state.curr_system, bid):
            st.session_state.edit_bid.description = bid.description
            st.session_state.edit_bid.pc_min = bid.pc_min
            st.session_state.edit_bid.pc_max = bid.pc_max
            st.session_state.edit_bid.balanced = bid.balanced
            st.session_state.edit_bid.suits = bid.suits
        else:
            st.session_state.message = {"type": "E", "message": f"Fail to change bid {bid.seq_str}"}
        st.session_state.edit_bid = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.edit_bid = None
        st.rerun()

@st.dialog("Confirm Deletion", dismissible=False)
def delete_bid_dialog():
    if not st.session_state.curr_system: return
    st.warning(f"Are you sure you want to delete thread **{st.session_state.delete_bid.seq_str}** ?")
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Yes 🗑"):
        if db.del_thread(st.session_state.curr_system, st.session_state.delete_bid):
            st.session_state.bids.remove(st.session_state.delete_bid)
            st.session_state.bids = [b for b in st.session_state.bids
                                     if not b.seq.startswith(st.session_state.delete_bid.full_seq)]
        else:
            st.session_state.message = {"type": "E", "message": f"Fail to delete bid {st.session_state.delete_bid.seq_str}"}
        st.session_state.delete_bid = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.delete_bid = None
        st.rerun()
