import streamlit as st
import json
import bcrypt
import os

# ----------------------------------------
# FILE NAME
# ----------------------------------------

USER_FILE = "users.json"


# ----------------------------------------
# INITIAL USER FILE
# ----------------------------------------

def create_default_admin():

    if not os.path.exists(USER_FILE):

        admin_pass = hash_password("admin123")

        users = {
            "admin": {
                "password": admin_pass,
                "role": "admin"
            }
        }

        save_users(users)


# ----------------------------------------
# LOAD USERS
# ----------------------------------------

def load_users():

    with open(USER_FILE, "r") as f:

        return json.load(f)


# ----------------------------------------
# SAVE USERS
# ----------------------------------------

def save_users(users):

    with open(USER_FILE, "w") as f:

        json.dump(users, f)


# ----------------------------------------
# HASH PASSWORD
# ----------------------------------------

def hash_password(password):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


# ----------------------------------------
# CHECK PASSWORD
# ----------------------------------------

def check_password(password, hashed):

    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )


# ----------------------------------------
# LOGIN
# ----------------------------------------

def login():

    st.title("🔐 Login System")

    username = st.text_input(
        "Username",
        key="login_user"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_pass"
    )

    if st.button("Login", key="login_btn"):

        users = load_users()

        if username in users and check_password(
            password,
            users[username]["password"]
        ):

            st.session_state.logged = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]

            st.success("Login successful")
            st.rerun()

        else:

            st.error("Invalid login")


# ----------------------------------------
# CHANGE PASSWORD
# ----------------------------------------

def change_password():

    st.subheader("🔑 Change Password")

    current = st.text_input(
        "Current Password",
        type="password",
        key="cp1"
    )

    new = st.text_input(
        "New Password",
        type="password",
        key="cp2"
    )

    confirm = st.text_input(
        "Confirm Password",
        type="password",
        key="cp3"
    )

    if st.button("Change Password", key="cp_btn"):

        users = load_users()

        username = st.session_state.username

        if not check_password(
            current,
            users[username]["password"]
        ):

            st.error("Wrong password")

        elif new != confirm:

            st.error("Passwords do not match")

        else:

            users[username]["password"] = hash_password(new)

            save_users(users)

            st.success("Password changed")


# ----------------------------------------
# ADMIN PANEL
# ----------------------------------------

def admin_panel():

    st.subheader("👨‍💼 Admin Panel")

    tab1, tab2 = st.tabs([
        "Add User",
        "Delete User"
    ])


    # ADD USER

    with tab1:

        new_user = st.text_input(
            "Username",
            key="au1"
        )

        new_pass = st.text_input(
            "Password",
            type="password",
            key="au2"
        )

        if st.button("Add User", key="au_btn"):

            users = load_users()

            if new_user in users:

                st.error("User exists")

            else:

                users[new_user] = {

                    "password": hash_password(new_pass),

                    "role": "user"

                }

                save_users(users)

                st.success("User added")



    # DELETE USER

    with tab2:

        users = load_users()

        user_del = st.selectbox(
            "Select user",
            list(users.keys()),
            key="du1"
        )

        if st.button("Delete", key="du_btn"):

            if user_del == "admin":

                st.error("Cannot delete admin")

            else:

                users.pop(user_del)

                save_users(users)

                st.success("Deleted")


# ----------------------------------------
# DASHBOARD
# ----------------------------------------

def dashboard():

    st.title(
        f"📊 Welcome {st.session_state.username}"
    )

    if st.button("Logout"):

        st.session_state.logged = False
        st.rerun()

    change_password()

    if st.session_state.role == "admin":

        admin_panel()


# ----------------------------------------
# MAIN
# ----------------------------------------

create_default_admin()

if "logged" not in st.session_state:

    st.session_state.logged = False


if st.session_state.logged:

    dashboard()

else:

    login()
