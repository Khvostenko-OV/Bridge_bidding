from config import st
import db
from dialogs import edit_bid_dialog, delete_system_dialog, delete_bid_dialog, clone_system_dialog
from models import Bid


def display_bid(bid: Bid):
    col1, col2 = st.columns([15, 1])
    with col1.expander(bid.to_str, False):
        for next_bid in bid.children:
            display_bid(next_bid)
        col3, col4 = st.columns([1, 12])
        if col3.button("➕", key=f"add_{bid.full_seq}"):
            db.add_answers(st.session_state.curr_system, bid.full_seq)
            st.rerun()
        if bid.children and col4.button("❌", key=f"del_{bid.full_seq}"):
            st.session_state.delete_bid = bid.children[-1].full_seq
    if col2.button("✏️", key=f"edit_{bid.full_seq}"):
        st.session_state.edit_bid = bid.full_seq

def main():
    st.set_page_config(page_title="Bridge bidding systems", layout="wide")
    if "edit_system" not in st.session_state:
        st.session_state.edit_system = None
    if "curr_system" not in st.session_state:
        st.session_state.curr_system = ""

    systems = db.systems()
    index = systems.index(st.session_state.curr_system) if st.session_state.curr_system in systems else None
    system_name = st.sidebar.selectbox("Choose system", systems, index=index, placeholder="Select")
    if not system_name and not st.session_state.edit_system:
        st.header("Bridge bidding")
    elif system_name and system_name != st.session_state.curr_system and not st.session_state.edit_system:
        st.session_state.curr_system = system_name
        st.rerun()

    if st.sidebar.button("Add System"):
        st.session_state.edit_system = "add"

#  Browse System
    if st.session_state.curr_system and not st.session_state.edit_system:
        sys_info = db.get_system(st.session_state.curr_system)
        col1, col2, col3 = st.columns([27, 3, 2])
        col1.subheader(sys_info.get("title", "---"))
        if col2.button("➕📄", key="clone_system_button", help=f"Clone System {sys_info.get('name', '')}"):
            st.session_state.edit_system = "clone"
        if col3.button("❌", key="delete_system_button", help=f"Delete System {sys_info.get('name', '')}"):
            st.session_state.edit_system = "delete"
        col1, col2 = st.columns([15, 1])
        with col1.expander(f"Version {sys_info.get('version')}", icon="📄"):
            st.markdown(f"{sys_info.get("description")}")
        if col2.button("✏️", key="edit_system_button", help=f"Edit System description"):
            st.session_state.edit_system = "edit"
            st.rerun()
        openings = db.build_tree(st.session_state.curr_system)
        for bid in openings:
            display_bid(bid)
        col1, col2 = st.columns([1, 15])
        if col1.button("➕", key="add_"):
            db.add_answers(st.session_state.curr_system)
            st.rerun()
        if openings and col2.button("❌", key="del_"):
            st.session_state.delete_bid = openings[-1].full_seq

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
                    if db.create_system(name, title, description, version):
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

#  Edit System info
    if st.session_state.edit_system == "edit":
        sys_info = db.get_system(st.session_state.curr_system)
        if sys_info:
            st.subheader(f"Edit System '{st.session_state.curr_system}'")
            with st.form("edit_system_form", enter_to_submit=False):
                title = st.text_input("Title", sys_info["title"], key="new_title")
                description = st.text_area("Description", sys_info["description"], key="new_descr")
                version = st.text_input("Version", sys_info["version"], key="new_ver")
                col1, col2 = st.columns([1, 9])
                if col1.form_submit_button("Save"):
                    if db.update_system(st.session_state.curr_system, title, description, version):
                        st.session_state.edit_system = None
                        st.rerun()
                    else:
                        st.error(f"Error. Can't update system '{st.session_state.curr_system}'!")
                if col2.form_submit_button("Cancel"):
                    st.session_state.edit_system = None
                    st.rerun()
        else:
            st.warning(f"System {st.session_state.curr_system} not found!")

# Open delete system dialog
    if st.session_state.edit_system == "delete":
        delete_system_dialog(st.session_state.curr_system)

# Open clone system dialog
    if st.session_state.edit_system == "clone":
        clone_system_dialog(st.session_state.curr_system)

# Open edit bid dialog
    if ("edit_bid" in st.session_state) and st.session_state.edit_bid:
        edit_bid_dialog(st.session_state.curr_system, st.session_state.edit_bid)

# Open delete bid with answers dialog
    if ("delete_bid" in st.session_state) and st.session_state.delete_bid:
        delete_bid_dialog(st.session_state.curr_system, st.session_state.delete_bid)

if __name__ == "__main__":
    db.init()
    main()
