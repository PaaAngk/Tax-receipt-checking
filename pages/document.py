import streamlit as st  # pip install streamlit
import database as db
import pandas as pd
import os
from datetime import date
import time
import streamlit.components.v1 as components
import base64

result = None
def timestap_from_date(date):
    return time.mktime(date.timetuple())

def search_by_number(doc_number):
    return db.get_document_search_by_number(str(doc_number))

def search_by_date_range( doc_type, first_date, second_date):
    return db.get_document_search_by_dateRange( 
        str(doc_type), 
        str(timestap_from_date(first_date)), 
        str(timestap_from_date(second_date)) 
    )


# ------------------------  Tabs  ------------------------ #
st.title("Поиск документов")

numberFind, dateRange = st.tabs(["По номеру", "По дате"])
with numberFind:
    doc_number_input = st.text_input("Номер документа")
    if st.button('Поиск по номеру'):
        result = None
        result = search_by_number(doc_number_input)

with dateRange:
    doc_type_input = st.selectbox("Выберите тип документа", [ "Все типы", "Авансовый отчёт"])
    first_date_input = st.date_input("С")
    second_date_input = st.date_input("По")

    if st.button('Поиск по дате'):
        result = None
        if doc_type_input == "Все типы":
            doc_type_input = None
            
        result = search_by_date_range(doc_type_input, first_date_input, second_date_input)

def check_null(item):
    return item if item != None else 'Нет данных'

# ------------------------  Table  ------------------------ #
if result:
    col_size =(1, 1, 1, 1, 1, 1, 1)
    colms = st.columns(col_size)
    fields = ["№", 'Создал', 'Дата', 'Номер документа', "Тип", "Статус"]
    for col, field_name in zip(colms, fields):
        col.write(field_name)

    for index, item in enumerate(result):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(col_size)
        with col1:
            st.write(index+1)
        with col2:
            col2.write(item['doc_creater'])
        with col3:
            col3.write(str(date.fromtimestamp( int(item['doc_date'])) ))
        with col4:
            col4.write(item['doc_number'])
        with col5:
            col5.write(item['doc_type'])
        with col6:
            col6.write( "Проверен" if check_null(item['status']) == 1 else "Не проверен" )
        with col7:            
            file_path = os.getcwd() + '/tempDir/'+item['file_name']
            file_name = item['file_name'].split('__')[-1]
            with open(file_path, "rb") as file:
                        base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                        file.close()
            href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="документ.pdf">Скачать PDF файл</a>'
            js_code = """
                <script>
                document.querySelector('.stButton button').addEventListener('click', function(e) {
                e.preventDefault();
                });
                </script>
                """
            print("nothing")
            st.markdown(href, unsafe_allow_html=True)
            st.markdown(js_code, unsafe_allow_html=True)
                
               


            
if result and len(result) == 0:
    st.warning("Документы не найдены")
    
st.write(result)


# ---- HIDE STREAMLIT STYLE ----
# hide_st_style = """
# <style>
# footer {visibility: hidden;}
# header {visibility: hidden;}
# </style>
# """
# st.markdown(hide_st_style, unsafe_allow_html=True)
# MainMenu {visibility: hidden;} 




# result_items = [s.values() for s in result]
# st.write(result_items)
# df_result = pd.DataFrame(
#     result_items, 
#     columns=["doc_create_date","Creater","Document date","Document number","Type","file_name","key","Status"]
# ).drop(["doc_create_date", "file_name","key"],axis=1)

# st.dataframe(df_result)