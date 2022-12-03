import pandas as pd  # pip install pandas openpyxl
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import os
import database as db
import qr_recognition as rec

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="QR Recognition", page_icon=":bar_chart:", layout="wide")

# --- DEMO PURPOSE ONLY --- #
placeholder = st.empty()
placeholder.info("username: Ivan; password: abc123")
# ------------------------- #

# --- USER AUTHENTICATION ---
users = db.fetch_all_users()

usernames = [user["key"] for user in users]
names = [user["name"] for user in users]
hashed_passwords = [user["password"] for user in users]

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "qr_reader", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    placeholder.empty()
# ------------------------- #


# ---- SIDEBAR ----

st.sidebar.title(f"Welcome {name}")
authenticator.logout("Logout", "sidebar")

# ------------------------- #


# ---- MAINPAGE ---- doc_type, doc_number, doc_date, doc_create_date, doc_creater
st.title("Read QR")
scanned_qr = []
left_column, right_column = st.columns(2)
with left_column:
    st.subheader("QR load:")
    # with open("exDoc.pdf", 'rb') as f:
    #     st.download_button("Download file", f, file_name='doc')
    with st.form("doc"):
        doc_type = st.selectbox("Choose document type", ["type1", "type2"])
        doc_number = st.text_input("Document number")
        doc_date = st.date_input("Document date")
        data = st.file_uploader("Upload a document")
        submitted = st.form_submit_button("Send document")
        if submitted:
            if data:
                with st.spinner("Please wait..."):
                    _, file_extension = data.type.split('/')
                    st.write(file_extension)
                    if file_extension == "pdf":
                        images = rec.get_image_from_pdf(data)
                        for pil_image in images:
                            scanned_qr.append(rec.read_qr(pil_image))
                    else:
                        scanned_qr.append(rec.run_read_image(data))
            else:
                st.warning("document")

with right_column:
    st.subheader("QR code scanning result:")
    if scanned_qr:
        for item in scanned_qr:
            if item["data"]:
                st.write(item["data"])
            else:
                st.error(item["warn"])
            st.image(item["image"])


# ------------------------- #



# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
