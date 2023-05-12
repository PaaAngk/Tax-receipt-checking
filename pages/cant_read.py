import streamlit as st 
from datetime import date
import time
import database as db

result = None
def timestap_from_date(date):
    return time.mktime(date.timetuple())

def get_avanc_report_by_status(status):
    return db.get_avanc_report_by_status((status))


st.title("Неподтверждённые авансовые отчёты")

status = 0
result = get_avanc_report_by_status(status)


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
            col6.write(item['status'] if item['status'] != None else 'Нет данных')
        with col7:
           print("1")
                
            
if result and len(result) == 0:
    st.warning("Документы не найдены")
    
st.write(result)
