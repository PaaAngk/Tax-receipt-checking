import pandas as pd  # pip install pandas openpyxl
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import os
import database as db
import qr_recognition as rec
from datetime import date
from multiprocessing import Pool
from time import time


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

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "qr_reader", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    placeholder.empty()
# ------------------------- #

# ---- SIDEBAR ----
if authentication_status:
    st.sidebar.title(f"Welcome {name}")
    authenticator.logout("Logout", "sidebar")
# ------------------------- #

# -------------- Functions ----------------------
def set_readed_image(scanned_qr, images):
    all_readed_qr = []
    not_readed_qr = []
    check_status = 1
    for scanned_item, image_item in zip(scanned_qr, images):
        if scanned_item and scanned_item['data']:
            if 'fn' in scanned_item['data']:
                all_readed_qr.append({
                    "title" : image_item["name"],
                    "status" : 1,
                    "data": scanned_item['data'],
                    "readed_image" : scanned_item['image'],
                })
            else:
                check_status = 0
                all_readed_qr.append({
                    "title" : image_item["name"],
                    "status" : "qr is not correct", 
                    "image" : image_item['image'],
                    "readed_image": scanned_item['image'],
                })

                not_readed_qr.append({
                    "title" : image_item["name"],
                    "image" : image_item['image'],
                    "readed_image": scanned_item['image'],
                    "status" : "qr is not correct"
                })
                
        else:
            check_status = 0
            all_readed_qr.append({
                "title" : image_item["name"],
                "status" : "can not read",
                "image" : image_item['image'],
                "readed_image": scanned_item['image'],
            })

            not_readed_qr.append({
                "title" : image_item["name"],
                "image" : image_item['image'],
                "readed_image": scanned_item['image'],
                "status" : "can not read"
            })
    return all_readed_qr, not_readed_qr, check_status


def save_uploadedfile(uploadedfile, doc_type, doc_number, doc_date, system_date):
    file_name = doc_type+"__"+doc_number+"__"+doc_date+"__"+system_date+"__"+uploadedfile.name
    with open(os.path.join("tempDir",file_name),"wb") as f:
         f.write(uploadedfile.getbuffer())
    return file_name

# ------------------------- #
 

# ---- MAINPAGE ----
if authentication_status:
    st.title("Read QR")
    scanned_qr = []
    not_readed_qr = []
    all_readed_qr = []
    check_status = None

    exec_time = None

    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader("QR load:")
        with st.form("doc"):
            doc_type = st.selectbox("Choose document type", ["type1", "type2"])
            doc_number = st.text_input("Document number")
            doc_date = st.date_input("Document date")
            data = st.file_uploader("Upload a document", type=["pdf", "tif", "tiff"])
            submitted = st.form_submit_button("Send document")
            
            progress_text = "Operation in progress. Please wait."
            
            if submitted:
                if data:
                    with st.spinner("Please wait..."):
                        _, file_extension = data.type.split('/')
                        if file_extension == "pdf":
                            if doc_type and doc_number and doc_date:

                                system_date = date.today().strftime("%d-%m-%Y")
                                doc_date = doc_date.strftime("%d-%m-%Y")
                                
                                #Read all image in file and scanned qr on each
                                try:
                                    images = rec.get_image_from_pdf(data)
                                except Exception:
                                    st.error("except document reading")

                                # images = [img["image"] for img in images]
                                # with Pool(1) as p:
                                #     scanned_qr = p.map(rec.read_qr, images)   

                                start_time = time()

                                progress_bar = st.progress(0)
                                image_count = 1 / len(images)
                                loading_bar_progress = 0
                                for pil_image in images:
                                    scanned_qr.append(rec.read_qr(pil_image["image"]))
                                    loading_bar_progress += image_count
                                    progress_bar.progress(loading_bar_progress if loading_bar_progress <= 1 else 1)

                                exec_time = time() - start_time

                                all_readed_qr, not_readed_qr, check_status = set_readed_image(scanned_qr, images)
                                
                                # file_name = save_uploadedfile(data, doc_type, doc_number, doc_date, system_date)
                                # db.insert_document(doc_type, doc_number, doc_date, system_date, name, file_name, check_status)
                            else:
                                st.warning("Please enter all required field")
                        else:
                            scanned_qr.append(rec.run_read_image(data))
                else:
                    st.warning("Please enter document")



# -------------------------------------------------------------------------- #
    with right_column:
        st.subheader("QR code scanning result:")
        readed = len(all_readed_qr)-len(not_readed_qr)
        st.write("Total: " + str(readed) +  " of " + str(len(all_readed_qr)) )
        st.write("Execution time: ",  exec_time, " seconds")
        if all_readed_qr:
            for item in all_readed_qr:

                if 'data' in item:
                  st.write(item["data"])
                if item["status"] != 1:
                    st.error(item["status"])
                st.image(item["readed_image"])
        if check_status:
            st.success("Проверка успешна!")



# ---- HIDE STREAMLIT STYLE ----
# hide_st_style = """
# <style>
# MainMenu {visibility: hidden;} 
# footer {visibility: hidden;}
# header {visibility: hidden;}
# </style>
# """
# st.markdown(hide_st_style, unsafe_allow_html=True)
