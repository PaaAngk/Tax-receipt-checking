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
from datetime import datetime
from io import BytesIO
import base64

st.set_page_config(page_title="Электронный архив", page_icon=":bar_chart:", layout="wide")


show_pages([
    Page("app.py", "Сохранить документ", ":notebook:"),
    Page("pages\document.py", "Найти документ", ":blue_book:"),
    Page("pages\cant_read.py", "Проверить вручную", ":blue_book:"),
    
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
    for scanned_page in scanned_qr:
        for scanned_item in scanned_page['result']:
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
                        "status" : "qr is not correct",
                        "page" : scanned_page['page'],
                        "coords" : scanned_item['coords'],
                    })
            else:
                check_status = 0
                all_readed_qr.append({
                    "status" : "can not read",
                    "readed_image": scanned_item['image'],
                })

                not_readed_qr.append({
                    "readed_image": scanned_item['image'],
                    "status" : "can not read",
                    "page" : scanned_page['page'],
                    "coords" : scanned_item['coords'],
                })
    return all_readed_qr, not_readed_qr, check_status


def save_uploadedfile(uploadedfile, doc_type, doc_number, doc_date, system_date):
    file_name = doc_type+"__"+doc_number+"__"+doc_date+"__"+system_date+"__"+uploadedfile.name
    with open(os.path.join("tempDir",file_name),"wb") as f:
        f.write(uploadedfile.getbuffer())
    return file_name

def parse_enter_document(enter_file):
    if enter_file is not None:
        _, file_extension = enter_file.split('.')
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
       
 
params = st.experimental_get_query_params()
path_file_check = params.get("file_path", [None])[0]
path=path_file_check
print("Здесь путь к файлу " + path_file_check)
type_with_all, doc_number_check, doc_date_check, system_date_check, enter_file_check = path_file_check.split("__")
type_with_all = os.path.basename(type_with_all)
doc_type_check = type_with_all.split("__")[0]
print(doc_type_check, doc_number_check, doc_date_check, system_date_check, enter_file_check )

with open(path_file_check, 'rb') as f:
    contents = f.read()
    #data = base64.b64encode(contents).decode('utf-8')
    #enter_file_check_file = f"data:application/pdf;base64,{data}"
    

#params = st.experimental_get_query_params()
path_file_check = params.get("file_path", None)
# ---- MAINPAGE ----
if authentication_status:
    st.title("Сохранение документа")
    not_readed_qr = []
    all_readed_qr = []
    check_status = None

    exec_time = None

    left_column, right_column = st.columns(2)
    with left_column:
        st.subheader("Загрузка документа:")
        with st.form("doc"):
            if params:
                doc_type_index = document_types.index(doc_type_check)
                doc_type = st.selectbox("Выберите тип документа", document_types, index=doc_type_index)
                doc_number = st.text_input("Номер документа", value = doc_number_check )
                doc_date = st.date_input("Дата", value=datetime.strptime(doc_date_check, "%d-%m-%Y"))
                #enter_file = st.file_uploader("Загрузить документ", type=["pdf", "tif", "tiff"], )
                
                ext=enter_file_check.split(".")[-1]
                print("Это расширение", ext)
                #enter_file = {"content": contents, "type": f"application/{ext}", "name": path_file_check}
                enter_file=path 
                
            else:
                doc_type = st.selectbox("Выберите тип документа", document_types)
                doc_number = st.text_input("Номер документа")
                doc_date = st.date_input("Дата")
                enter_file = st.file_uploader("Загрузить документ", type=["pdf", "tif", "tiff"], )
               
            submitted = st.form_submit_button("Сохранить")

            
            progress_text = "Операция выполняется. Пожалуйста, подождите"
            
            if submitted:
                if enter_file:
                    scanned_qr = []
                    if doc_type and doc_number and doc_date:
                        doc_date_to_save = doc_date
                        system_date = date.today().strftime("%d-%m-%Y")

                        if doc_type=="Авансовый отчёт":
                            with st.spinner("Пожалуйста, подождите..."):
                                parsed_pages = parse_enter_document(enter_file)
                                if (parsed_pages):
                                    #Read all image in file and scanned qr on each
                                    for page in parsed_pages:
                                        scanned_qr.append({
                                            "page":page["page"],
                                            "result": rec.read_qr(page)
                                        })

                                    all_readed_qr, not_readed_qr, check_status = set_readed_image(scanned_qr)
                                    not_readet_data = [{
                                                        "page" : qr['page'],
                                                        "coords" : qr['coords'],
                                                    } for qr in not_readed_qr ] if len(not_readed_qr) > 0 else None

                                    file_name = save_uploadedfile(enter_file, doc_type, doc_number, doc_date.strftime("%d-%m-%Y"), system_date)
                                    db.insert_document(doc_type, doc_number, doc_date_to_save, system_date, name, file_name, check_status, not_readet_data) 
                        else: 
                            file_name = save_uploadedfile(enter_file, doc_type, doc_number, doc_date.strftime("%d-%m-%Y"), system_date)
                            db.insert_document(doc_type, doc_number, doc_date_to_save, system_date, name, file_name, None)                     
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




