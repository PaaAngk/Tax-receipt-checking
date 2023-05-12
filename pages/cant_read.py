import streamlit as st 
from datetime import date
import time
import database as db
import os
import streamlit.components.v1 as components
import base64

result = None
def timestap_from_date(date):
    return time.mktime(date.timetuple())

def get_avanc_report_by_status(status):
    print(status)
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
           file_path = os.getcwd() + '/tempDir/'+item['file_name']
           with open(file_path, "rb") as file:
                base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                    
                components.html(f"""
                            <html>
                                <button id="elem" style="background-color: transparent; border: none; color: white; "> Просмотреть документ </button>
                                <script> 
                                    function display() {{
                                        console.log("j");
                                        var byteArray = new Uint8Array(atob("{base64_pdf}").split('').map(function(char) {{
                                            return char.charCodeAt(0);
                                        }}));
                                        var file = new Blob([byteArray], {{ type: 'application/pdf' }});
                                        var fileURL = URL.createObjectURL(file);
                                        window.open(fileURL);
                                    }};
                                    window.onload = function() {{
                                        document.getElementById("elem").onclick = display;
                                    }};
                                </script>
                            </html>
                        """) 
                file.close() 

        col_size_pg=(1,2,2)
        colms_pg = st.columns(col_size_pg)
        fields_pg = ["№", 'Страница']
        for col, field_name in zip(colms_pg, fields_pg):
            col.write(field_name)
        kol_pages=[]
        for page in kol_pages:
            col1_pg, col2_pg, col3_pg = st.columns(col_size_pg)
            with col1_pg:
                st.write(index+1)
            with col2_pg:#здесь ссылка на просмотре страницы с чеком
                print()
            with col3_pg:#здесь кнопка на подтверждание
                print()


        
                
            
if result and len(result) == 0:
    st.warning("Документы не найдены")
    
st.write(result)
