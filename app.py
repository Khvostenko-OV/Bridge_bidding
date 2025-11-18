from config import st
import db
from dialogs import edit_bid_dialog, delete_system_dialog, delete_bid_dialog, clone_system_dialog, login_dialog, \
    register_dialog
from models import Bid
from utils import repl_str


def display_bid(bid: Bid, opps=False, can_edit=False):
    if can_edit:
        col1, col2 = st.columns([19, 1])
    else:
        col1 = st.columns(1)[0]
        col2 = None
    with col1.expander(bid.to_markdown(opps), False, ):
        for next_bid in bid.children:
            display_bid(next_bid, opps, can_edit)
        if can_edit:
            col3, col4 = st.columns([1, 9])
            if col3.button("➕", key=f"add_{bid.full_seq}"):
                db.add_answer(st.session_state.curr_system, bid.full_seq, opps)
                st.rerun()
            if bid.children and col4.button("❌", key=f"del_{bid.full_seq}"):
                st.session_state.delete_bid = bid.children[-1].full_seq
    if can_edit and col2.button("✏️", key=f"edit_{bid.full_seq}"):
        st.session_state.edit_bid = bid.full_seq

def main():
    st.set_page_config(page_title="Bridge bidding systems", layout="wide")
    if "user" not in st.session_state:
        st.session_state.user = ""
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "opps" not in st.session_state:
        st.session_state.opps = False
    if "show_login" not in st.session_state:
        st.session_state.show_login = "login"
    if "edit_system" not in st.session_state:
        st.session_state.edit_system = None
    if "curr_system" not in st.session_state:
        st.session_state.curr_system = ""

    st.sidebar.markdown(f"👤 :blue-background[{st.session_state.username or st.session_state.user or '*Anonym*'}]")
    if st.sidebar.button(f"{'Logout' if st.session_state.user else 'Login'}", key="login_button"):
        st.session_state.curr_system = ""
        st.session_state.user = ""
        st.session_state.username = ""
        st.session_state.opps = False
        st.session_state.show_login = "login"
        st.rerun()


    systems = db.systems()
    index = systems.index(st.session_state.curr_system) if st.session_state.curr_system in systems else None
    system_name = st.sidebar.selectbox("Choose system", systems, index=index, placeholder="Select")
    if system_name and system_name != st.session_state.curr_system and not st.session_state.edit_system:
        st.session_state.curr_system = system_name
        if st.session_state.user:
            db.change_user(st.session_state.user, st.session_state.curr_system)
        st.rerun()

    if st.session_state.show_login == "login":
        login_dialog()

    if st.session_state.show_login == "signup":
        register_dialog()

    st.session_state.opps = st.sidebar.toggle("With opps", value=st.session_state.opps, key="opps_switch")

    if st.session_state.user and st.sidebar.button("Add System"):
        st.session_state.edit_system = "add"

    sys_info = db.get_system(st.session_state.curr_system)
    if sys_info is None:
        st.header("Bridge bidding")
        if st.session_state.curr_system:
            st.warning(f"Can't read System {st.session_state.curr_system}")
    else:
#  Browse System
        if not st.session_state.edit_system:
            can_edit = st.session_state.user == sys_info["owner"]
            col1, col2, col3 = st.columns([35, 3, 2])
            col1.subheader(sys_info["title"])
            if st.session_state.user and col2.button("➕📄", key="clone_system_button", help=f"Clone System"):
                st.session_state.edit_system = "clone"
            if can_edit and col3.button("❌", key="delete_system_button", help=f"Delete System"):
                st.session_state.edit_system = "delete"
            if can_edit:
                col1, col2 = st.columns([19, 1])
            else:
                col1 = st.columns(1)[0]
            with col1.expander(
                    f"Version {sys_info['version']} | Created by *{sys_info['owner_name'] or sys_info['owner']}*",
                    icon="📄"):
                st.markdown(f"{sys_info["description"]}")
            if can_edit and col2.button("✏️", key="edit_system_button", help=f"Edit System description") and st.session_state.user:
                st.session_state.edit_system = "edit"
                st.rerun()
            openings = db.build_tree(st.session_state.curr_system, "", st.session_state.opps)
            for bid in openings:
                display_bid(bid, st.session_state.opps, can_edit)
            if can_edit:
                col1, col2 = st.columns([1, 9])
                if col1.button("➕", key="add_"):
                    db.add_answer(st.session_state.curr_system)
                    st.rerun()
                if openings and col2.button("❌", key="del_"):
                    st.session_state.delete_bid = openings[-1].full_seq

#  Edit System info
        if st.session_state.edit_system == "edit":
            st.subheader(f"Edit System '{st.session_state.curr_system}'")
            with st.form("edit_system_form", enter_to_submit=False):
                title = st.text_input("Title", sys_info["title"], key="new_title")
                version = st.text_input("Version", sys_info["version"], key="new_ver")
                description = st.text_area("Description", sys_info["description"], height="content", key="new_descr")
                col1, col2 = st.columns([1, 9])
                if col1.form_submit_button("Save"):
                    if db.update_system(st.session_state.curr_system, repl_str(title), repl_str(description), version):
                        st.session_state.edit_system = None
                        st.rerun()
                    else:
                        st.error(f"Error. Can't update system '{st.session_state.curr_system}'!")
                if col2.form_submit_button("Cancel"):
                    st.session_state.edit_system = None
                    st.rerun()

    #  Create new System
    if st.session_state.edit_system == "add":
        st.subheader("Add New System")
        with st.form("add_system_form", enter_to_submit=False):
            name = st.text_input("Short name", key="name")
            title = st.text_input("Title", key="title")
            description = st.text_area("Description", key="descr")
            version = st.text_input("Version", "1.0", key="ver")
            col1, col2 = st.columns([1, 9])
            if col1.form_submit_button("Save"):
                if name:
                    if db.create_system(name, title, description, version, st.session_state.user):
                        st.session_state.curr_system = name
                        st.session_state.edit_system = None
                        st.rerun()
                    else:
                        st.error(f"Error. Can't create system '{name}'!")
                else:
                    st.warning("Please enter Short name")
            if col2.form_submit_button("Cancel"):
                st.session_state.edit_system = None
                st.rerun()

# Open delete system dialog
    if st.session_state.edit_system == "delete":
        delete_system_dialog(st.session_state.curr_system)

# Open clone system dialog
    if st.session_state.edit_system == "clone":
        clone_system_dialog(st.session_state.curr_system)

# Open edit bid dialog
    if ("edit_bid" in st.session_state) and st.session_state.edit_bid:
        edit_bid_dialog(st.session_state.curr_system, st.session_state.edit_bid)

# Open delete bid dialog
    if ("delete_bid" in st.session_state) and st.session_state.delete_bid:
        delete_bid_dialog(st.session_state.curr_system, st.session_state.delete_bid)

if __name__ == "__main__":
    db.init()
    main()
