import streamlit as st 
from datetime import date
import time
import database as db
import os
import streamlit.components.v1 as components
import base64
import PyPDF2


result = None
def timestap_from_date(date):
    return time.mktime(date.timetuple())

def get_avanc_report_by_status(status):
    print(status)
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

#if st.button("Перейти на другую страницу", key=9):
    # # Получаем абсолютный путь к текущему файлу
    # current_file_path = os.path.abspath(__file__)
    # # Получаем часть пути до имени проекта
    # root_path = os.path.dirname(os.path.dirname(current_file_path))
    # # Формируем относительный путь к нужной странице
    # page_path = os.path.join(root_path, "pages\\", "document.py")
    # print(current_file_path)
    # print(page_path)
    #             # Устанавливаем параметры запроса для перехода на другую страницу
    # st.experimental_set_query_params(page="Найти документ")
    #             # Перезапускаем приложение
    # st.experimental_rerun()
# html_code="""
                             
#         <html>
#         <a href="http://localhost:8501/Найти документ"></a>                     
#         <script> 
#      window.location.assign = "http://localhost:8501/Найти документ";
#      <a href
#         </script>
#         </html>
#       """
# components.html(html_code)
# hreff=f'<a href="http://localhost:8501/Найти документ"></a> '
# href1 = f'<a style="background-color: transparent; border: none; color: white;" href="http://localhost:8501">Скачать PDF файл</a>'
# st.markdown(href1, unsafe_allow_html=True)


def print_box_in_pdf(file, boxes):
    pdfReader = PyPDF2.PdfReader(file)

    pdfReader.getPage(1)
    x, y,w,h = 100, 100, 200, 200
    
     

# if "page" in st.experimental_get_query_params():
#     if st.experimental_get_query_params()["page"] == page_path:
#         st.write("Вы перешли на другую страницу")
# ------------------------  Table  ------------------------ #
if result:
    col_size =(1, 1, 1, 1, 1, 1, 2, 2,1)
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
            try:
                file_path = os.getcwd() + '/tempDir/'+item['file_name']
                with open(file_path, "rb") as file:
                        base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                        components.html(f"""
                                    <html>
                                        <button id="elem" style="background-color: transparent; border: none; color: white; text-decoration: underline;"> Просмотреть документ </button>
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
            except FileNotFoundError:
                st.write("Не удалось найти файл")
        with col8:
            try:
                file_name = item['file_name'].split('__')[-1]
                with open(file_path, "rb") as file:
                            base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                            file.close()
                href = f'<a style="background-color: transparent; border: none; color: white;" href="data:application/pdf;base64,{base64_pdf}" download="{file_name}.pdf">Скачать PDF файл</a>'
                no_reload()
                #print("nothing")
                st.markdown(href, unsafe_allow_html=True)
            except FileNotFoundError:
                st.write("Не удалось найти файл")
        # with col9:
        #      # Создаем объект состояния
        #     st.session_state['file_contents']=None

        #         # Если файл загружен, сохраняем его содержимое в SessionState
        #     with open(file_path, "rb") as file:
        #         file_contents = file.read()
        #         st.session_state['file_contents'] = file_contents
        #         file.close()
            


        
                
            
if result and len(result) == 0:
    st.warning("Документы не найдены")
    
# st.write(result)
