from bidding import logout, get_answers, add_answer, swap_system, save_system, load_system
from config import st, README
import db
from dialogs import login_dialog, register_dialog
from dialogs import edit_bid_dialog, delete_system_dialog, delete_bid_dialog, clone_system_dialog
from models import Bid
from utils import repl_str


def display_bid(bid: Bid, can_edit=False):
    if can_edit:
        col1, col2 = st.columns([19, 1])
    else:
        col1 = st.columns(1)[0]
        col2 = None
    with col1.expander(bid.to_markdown(st.session_state.opps), False, ):
        answers = get_answers(bid.full_seq + ("" if st.session_state.opps else ".0"))
        for next_bid in answers:
            display_bid(next_bid, can_edit)
        if can_edit:
            col3, col4 = st.columns([1, 9])
            if col3.button("➕", key=f"add_{bid.full_seq}") and add_answer(bid):
                st.rerun()
            if answers and col4.button("❌", key=f"del_{bid.full_seq}"):
                st.session_state.delete_bid = answers[-1]
    if can_edit and col2.button("✏️", key=f"edit_{bid.full_seq}"):
        st.session_state.edit_bid = bid

def main():
    if "show_login" not in st.session_state:
        logout()

    st.sidebar.markdown(f"👤 :blue-background[{st.session_state.username or '*Anonym*'}]")
    if st.sidebar.button(f"{'Logout' if st.session_state.user else 'Login'}", key="login_button"):
        logout()
        st.rerun()

    if st.session_state.show_login == "login":
        login_dialog()

    if st.session_state.show_login == "signup":
        register_dialog()

    index = st.session_state.systems.index(st.session_state.curr_system) \
        if st.session_state.curr_system in st.session_state.systems else None
    system_name = st.sidebar.selectbox("Choose system",st.session_state.systems,
                                       index=index,
                                       placeholder="Select",
                                       disabled=st.session_state.edit_system is not None,
                                       )
    if system_name and system_name != st.session_state.curr_system:
        swap_system(system_name)
        st.rerun()

    st.session_state.opps = st.sidebar.toggle("With opps", value=st.session_state.opps, key="opps_switch")

    if st.session_state.user and st.sidebar.button("Add System", key=f"add_sys_button"):
        st.session_state.edit_system = "add"
        st.rerun()

    if st.session_state.is_admin and st.sidebar.button("Save System", key="save_sys_button"):
        save_system()

    if st.session_state.is_admin:
        uploader = st.sidebar.file_uploader("Load System", type="csv",
                                            key="file_button" + str(st.session_state.loads), help="Choose .csv file")
        if uploader and st.sidebar.button("Load", key="load_sys_button", help="Load System from file"):
            load_system(uploader.name)
            st.session_state.loads += 1
            uploader.close()
            st.rerun()

    if st.session_state.message:
        match st.session_state.message["type"]:
            case "I":
                st.info(st.session_state.message["message"])
            case "W":
                st.warning(st.session_state.message["message"])
            case "E":
                st.error(st.session_state.message["message"])
            case "S":
                st.success(st.session_state.message["message"])
    st.session_state.message = None

    if st.session_state.sys_info is None:
        st.header("Bridge Bidding")
        if st.session_state.curr_system:
            st.warning(f"Can't read System **{st.session_state.curr_system}**")
        st.markdown(README)
    else:
#  Browse System
        if not st.session_state.edit_system:
            can_edit = st.session_state.user == st.session_state.sys_info["owner"]
            col1, col2, col3 = st.columns([35, 3, 2])
            col1.subheader(st.session_state.sys_info["title"])
            if st.session_state.user and col2.button("➕📄", key="clone_system_button", help=f"Clone System"):
                st.session_state.edit_system = "clone"
            if can_edit and col3.button("❌", key="delete_system_button", help=f"Delete System"):
                st.session_state.edit_system = "delete"
            if can_edit:
                col1, col2 = st.columns([19, 1])
            else:
                col1 = st.columns(1)[0]
            with col1.expander(
                    f"Version {st.session_state.sys_info['version']} | "
                    f"Created by *{st.session_state.sys_info['owner_name']}*",
                    icon="📄"):
                st.markdown(f"{st.session_state.sys_info["description"]}")
            if can_edit and col2.button("✏️", key="edit_system_button", help=f"Edit System description"):
                st.session_state.edit_system = "edit"
                st.rerun()
            openings = get_answers()
            for bid in openings:
                display_bid(bid, can_edit)
            if can_edit:
                col1, col2 = st.columns([1, 9])
                if col1.button("➕", key="add_") and add_answer():
                    st.rerun()
                if openings and col2.button("❌", key="del_"):
                    st.session_state.delete_bid = openings[-1]

#  Edit System info
        if st.session_state.edit_system == "edit":
            st.subheader(f"Edit System '{st.session_state.curr_system}'")
            with st.form("edit_system_form", enter_to_submit=False):
                title = st.text_input("Title", st.session_state.sys_info["title"], key="new_title")
                version = st.text_input("Version", st.session_state.sys_info["version"], key="new_ver")
                description = st.text_area("Description", st.session_state.sys_info["description"], height="content", key="new_descr")
                col1, col2 = st.columns([1, 9])
                if col1.form_submit_button("Save"):
                    if db.update_system(st.session_state.curr_system, repl_str(title), repl_str(description), version):
                        st.session_state.edit_system = None
                        st.session_state.sys_info = db.get_system_info(st.session_state.curr_system)
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
            if col1.form_submit_button("Create"):
                if name:
                    if db.create_system(name, title, description, version, st.session_state.user):
                        swap_system(name)
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
        delete_system_dialog()

# Open clone system dialog
    if st.session_state.edit_system == "clone":
        clone_system_dialog()

# Open edit bid dialog
    if st.session_state.edit_bid:
        edit_bid_dialog()

# Open delete bid dialog
    if st.session_state.delete_bid:
        delete_bid_dialog()

if __name__ == "__main__":
    # db.init()
    st.set_page_config(page_title="Bridge bidding systems", layout="wide")
    main()
