import pandas as pd  # pip install pandas openpyxl
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import os
import database as db
import qr_recognition as rec
from datetime import date
from multiprocessing import Pool
import time
from st_pages import Page, show_pages
import datetime

st.set_page_config(page_title="Электронный архив", page_icon=":bar_chart:", layout="wide")


show_pages([
    Page("app.py", "Сохранить документ", ":notebook:"),
    Page("pages\document.py", "Найти документ", ":blue_book:"),
    
])

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
    st.error("Логин/пароль неверный")

if authentication_status == None:
    st.warning("Пожалуйста, введите имя пользователя и пароль")

if authentication_status:
    placeholder.empty()
# ------------------------- #

document_types = [
"Авансовый отчёт",
"Акт сверки взаиморасчетов",
"Ввод начальных остатков по ОС",
"Изменение параметров начисления амортизации ОС",
"Инвентаризация наличных денежных средств",
"Инвентаризация товаров отданных на комиссию",
"Корректировка начисленной амортизации",
"Корректировка прочих затрат",
"Начисление процентов к уплате",
"Операция (бухгалтерский и налоговый учет)",
"Отчет агента об оплатах",
"Отчет комитенту/принципалу о продажах",
"Передача НМА",
"Передача ОС в аренду",
"Передача товаров",
"Подготовка к передаче ОС",
"Поступление ОС из аренды",
"Поступление товаров из переработки",
"Приходный кассовый ордер",
"Расчет резерва по ТМЦ (БУ)",
"Реализация имущества учитываемого на забалансе",
"Списание незавершенного производства",
"Списание НЗС",
"Счет-фактура выданный",
]


# ------------- SIDEBAR ------------ #
if authentication_status:
    st.sidebar.title(f"Добро пожаловать, {name}")
    authenticator.logout("Выйти", "sidebar")
# ------------------------- #


# -------------- Functions ----------------------
def set_readed_image(scanned_qr):
    all_readed_qr = []
    not_readed_qr = []
    check_status = 1
    for scanned_item in scanned_qr:
        if scanned_item and scanned_item['data']:
            if 'fn' in scanned_item['data']:
                all_readed_qr.append({
                    "status" : 1,
                    "data": scanned_item['data'],
                    "readed_image" : scanned_item['image'],
                })
            else:
                check_status = 0
                all_readed_qr.append({
                    "status" : "qr is not correct", 
                    # "image" : scanned_item["image"],
                    "readed_image": scanned_item['image'],
                })

                not_readed_qr.append({
                    # "image" : scanned_item["image"],
                    "readed_image": scanned_item['image'],
                    "status" : "qr is not correct"
                })
                
        else:
            check_status = 0
            all_readed_qr.append({
                "status" : "can not read",
                # "image" : scanned_item["image"],
                "readed_image": scanned_item['image'],
            })

            not_readed_qr.append({
                # "image" : scanned_item["image"],
                "readed_image": scanned_item['image'],
                "status" : "can not read"
            })
    return all_readed_qr, not_readed_qr, check_status


def save_uploadedfile(uploadedfile, doc_type, doc_number, doc_date, system_date):
    file_name = doc_type+"__"+doc_number+"__"+doc_date+"__"+system_date+"__"+uploadedfile.name
    with open(os.path.join("tempDir",file_name),"wb") as f:
        f.write(uploadedfile.getbuffer())
    return file_name

def parse_enter_document(enter_file):
    _, file_extension = enter_file.type.split('/')
    if file_extension == "pdf":
        try:
            return rec.get_images_from_pdf(enter_file)
        except Exception:
            st.error("except document reading")
            return

    if file_extension == "tif" or file_extension == "tiff":
        try:
            return rec.get_images_from_tif(enter_file)
        except Exception:
            st.error("except document reading")
            return
 

# ---- MAINPAGE ----
if authentication_status:
    st.title("Сохранение документа")
    scanned_qr = []
    not_readed_qr = []
    all_readed_qr = []
    check_status = None

    exec_time = None

    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader("Загрузка документа:")
        with st.form("doc"):
            doc_type = st.selectbox("Выберите тип документа", document_types)
            doc_number = st.text_input("Номер документа")
            doc_date = st.date_input("Дата")
            enter_file = st.file_uploader("Загрузить документ", type=["pdf", "tif", "tiff"], )
            submitted = st.form_submit_button("Сохранить")
            
            progress_text = "Операция выполняется. Пожалуйста, подождите"
            
            if submitted:
                if enter_file:
                    if doc_type and doc_number and doc_date:
                        doc_date_to_save = time.mktime(doc_date.timetuple())
                        system_date = date.today().strftime("%d-%m-%Y")

                        if doc_type=="Авансовый отчёт":
                            with st.spinner("Пожалуйста, подождите..."):
                                images = parse_enter_document(enter_file)
                                if (images):
                                    #Read all image in file and scanned qr on each
                                    for pil_image in images:
                                        scanned_qr.extend(rec.read_qr(pil_image["image"]))

                                    all_readed_qr, not_readed_qr, check_status = set_readed_image(scanned_qr)

                                    # file_name = save_uploadedfile(enter_file, doc_type, doc_number, doc_date.strftime("%d-%m-%Y"), system_date)
                                    # db.insert_document(doc_type, doc_number, doc_date_to_save, system_date, name, file_name, check_status) 
                        else: 
                            file_name = save_uploadedfile(enter_file, doc_type, doc_number, doc_date.strftime("%d-%m-%Y"), system_date)
                            db.insert_document(doc_type, doc_number, doc_date_to_save, system_date, name, file_name)                     
                    else:
                        st.warning("Пожалуйста, заполните все поля")
                else:
                    st.warning("Пожалуйста, прикрепите документ")

# -------------------------------------------------------------------------- #
    with right_column:
        st.subheader("Результат сканирования:")
        readed = [ l['status'] for l in all_readed_qr]
        st.write("Всего: " + str(readed.count(1)) +  " из " + str(len(all_readed_qr)) )
        # st.write("Время обработки: ",  exec_time, " секунд")
        # if all_readed_qr:
        #     for item in all_readed_qr:
        #         if 'data' in item:
        #           st.write(item["data"])
        #         if item["status"] != 1:
        #             st.error(item["status"])
        #         st.image(item["readed_image"])
        if not_readed_qr:
            for item in not_readed_qr:
                if 'data' in item:
                  st.write(item["data"])
                if item["status"] != 1:
                    st.error(item["status"])
                st.image(item["readed_image"])
        if check_status:
            st.success("Проверка успешна!")




