import streamlit as st 
from datetime import date
import time
import database as db
import os
import streamlit.components.v1 as components
import base64
st.set_page_config(page_title="Неподтверждённые авансовые отчёты", page_icon=":bar_chart:", layout="wide")
import PyPDF2


result = None
def timestap_from_date(date):
    return time.mktime(date.timetuple())

def get_avanc_report_by_status(status):
    return db.get_avanc_report_by_status((status))

def no_reload():
     js_code = """
                <script>
                document.querySelector('.stButton button').addEventListener('click', function(e) {
                e.preventDefault();
                });
                </script>
                """
     st.markdown(js_code, unsafe_allow_html=True)

st.title("Неподтверждённые авансовые отчёты")

status = 0
result = get_avanc_report_by_status(status)

def js_redirect(url):
    js = f"window.location.href = '{url}'"
    html = f'<html><head><meta http-equiv="refresh" content="0;url={url}"></head><body></body></html>'
    st.markdown(html, unsafe_allow_html=True)


def print_box_in_pdf(file, boxes):
    pdfReader = PyPDF2.PdfReader(file)
    pdfReader.getPage(1)
    x, y,w,h = 100, 100, 200, 200
    
     
# if "page" in st.experimental_get_query_params():
#     if st.experimental_get_query_params()["page"] == page_path:
#         st.write("Вы перешли на другую страницу")
# ------------------------  Table  ------------------------ #
if result:
    col_size =(1, 1, 1, 1, 1, 1, 2, 2, 1)
    colms = st.columns(col_size)
    fields = ["№", 'Создал', 'Дата', 'Номер документа', "Тип", "Статус"]
    for col, field_name in zip(colms, fields):
        col.write(field_name)

    for index, item in enumerate(result):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(col_size)
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
            if st.button("Просмотреть документ", key=index):
                try:
                    file_path = os.getcwd() + '/tempDir/'+item['file_name']
                    with open(file_path, "rb") as file:
                        base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                        file.close() 
                        components.html(f"""
                                    <html>
                                        <script> 
                                            var byteArray = new Uint8Array(atob("{base64_pdf}").split('').map(function(char) {{
                                                return char.charCodeAt(0);
                                            }}));
                                            var file = new Blob([byteArray], {{ type: 'application/pdf' }});
                                            var fileURL = URL.createObjectURL(file);
                                            window.open(fileURL);
                                        </script>
                                    </html>
                                """) 
                        
                except FileNotFoundError:
                    st.write("Не удалось найти файл")
        with col8:
            if st.button("Скачать PDF файл", key=index+100):
                try:
                    file_path = os.getcwd() + '/tempDir/'+item['file_name']
                    file_name = item['file_name'].split('__')[-1]
                    with open(file_path, "rb") as file:
                        base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                        file.close()
                        components.html(f"""
                                    <html>
                                        <script> 
                                            var link = document.createElement("a");
                                            link.setAttribute('download', "{file_name}");
                                            link.setAttribute('href', "data:application/pdf;base64,{base64_pdf}");
                                            link.click();
                                            link.remove();
                                        </script>
                                    </html>
                                """) 
                except FileNotFoundError:
                    st.write("Не удалось найти файл")
        with col9:
             if st.button("Проверить повторно", key=index+1):
                st.experimental_set_query_params(
                file_path=file_path
            )

            # Получаем параметры запроса
                params = st.experimental_get_query_params()

            # Печатаем параметры запроса
                print(params)
                js_redirect("http://localhost:8501/%22)

            


        
                
            
if result and len(result) == 0:
    st.warning("Документы не найдены")
    
# st.write(result)
