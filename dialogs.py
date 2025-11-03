from config import st
import db
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
            st.session_state.username = log["username"]
            st.session_state.curr_system = log["system"]
            st.session_state.show_login = ""
            st.rerun()
    if col2.button("Register"):
        st.session_state.show_login = "signup"
        st.rerun()
    if col3.button("Read only"):
        st.session_state.user = ""
        st.session_state.username = ""
        st.session_state.curr_system = ""
        st.session_state.show_login = ""
        st.rerun()

@st.dialog("New user", dismissible=False)
def register_dialog():
    login = st.text_input("Login", key="lgn")
    password = st.text_input("Password", type="password", key="psw")
    username = st.text_input("Username", key="usrnm")
    col1, col2, col3 = st.columns([1, 1, 2])
    if col1.button("Create") and login and password:
        err = db.add_user(login, password, username)
        if err:
            st.error(err)
        else:
            st.session_state.user = login
            st.session_state.username = username
            st.session_state.curr_system = ""
            st.session_state.show_login = ""
            st.rerun()
    if col2.button("Login"):
        st.session_state.show_login = "login"
        st.rerun()
    if col3.button("Read only"):
        st.session_state.user = ""
        st.session_state.username = ""
        st.session_state.curr_system = ""
        st.session_state.show_login = ""
        st.rerun()

@st.dialog("Confirm Deletion", dismissible=False)
def delete_system_dialog(sys_name: str):
    if not sys_name: return
    st.warning(f"Are you sure you want to delete System '**{sys_name}**'?")
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Yes 🗑"):
        db.delete_system(sys_name)
        if st.session_state.curr_system == sys_name:
            st.session_state.curr_system = ""
        st.session_state.edit_system = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.edit_system = None
        st.rerun()

@st.dialog("Clone system", dismissible=False)
def clone_system_dialog(sys_name: str):
    if not sys_name: return
    st.subheader(f"Create a copy of '**{sys_name}**'")
    new_name = st.text_input("New short name", key="new_name")
    if new_name in db.systems():
        st.error("This name is already in use!")
        new_name = ""
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Yes") and new_name:
        if db.clone_system(sys_name, new_name, st.session_state.user):
            st.session_state.curr_system = new_name
        st.session_state.edit_system = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.edit_system = None
        st.rerun()


@st.dialog("Edit bid", width="medium", dismissible=False)
def edit_bid_dialog(sys_name: str, seq: str):
    if not sys_name: return
    bid = db.fetch_bid(sys_name, seq)
    if not bid: return
    st.subheader(bid.seq_str)
    desc = st.text_input("Description", value=bid.description, key="bid_description")
    col_save, col_no = st.columns(2)
    if col_save.button("✅ Save"):
        bid.description = repl_str(desc)
        db.update_bid(sys_name, bid)
        st.session_state.edit_bid = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.edit_bid = None
        st.rerun()

@st.dialog("Confirm Deletion", dismissible=False)
def delete_bid_dialog(sys_name: str, seq: str):
    if not sys_name: return
    bid = db.fetch_bid(sys_name, seq)
    if not bid: return
    st.warning(f"Are you sure you want to delete thread **{bid.seq_str}** ?")
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Yes 🗑"):
        db.del_thread(sys_name, bid.full_seq)
        st.session_state.delete_bid = None
        st.rerun()
    if col_no.button("❌ Cancel"):
        st.session_state.delete_bid = None
        st.rerun()
