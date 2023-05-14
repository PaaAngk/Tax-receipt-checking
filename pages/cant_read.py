from io import BytesIO
import streamlit as st 
from datetime import date
import time
import database as db
import os
import streamlit.components.v1 as components
import base64
from pypdf import PdfReader, PdfWriter, PaperSize
from pypdf.generic import AnnotationBuilder

st.set_page_config(page_title="Неподтверждённые авансовые отчёты", page_icon=":bar_chart:", layout="wide")

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
    html = f'<html><head><meta http-equiv="refresh" content="0;url={url}"></head><body></body></html>'
    st.markdown(html, unsafe_allow_html=True)

def create_rect(coords):
    return AnnotationBuilder.rectangle(
        rect=(coords["xmin"]/2, coords["ymin"]/6, coords["xmax"]/1.7, coords["ymax"]/4.5),
    )

# {"coords": {
#       "xmax": 912.7886352539,
#       "xmin": 691.9747924805,
#       "ymax": 2095.96484375,
#       "ymin": 1860.0693359375
#     },
#     "page": 3}
def print_box_in_pdf(file, not_readed_data):
    pdfReader = PdfReader(file)
    writer = PdfWriter()
    writer.append_pages_from_reader(pdfReader)
    print("!!!!!!!!!!!!!!!!!!!!!!!")
    print(not_readed_data)
    for item in not_readed_data:
        annotation = create_rect(item['coords'])
        print(annotation)
        writer.add_annotation(page_number=int(item['page']), annotation=annotation)
    with BytesIO() as bytes_stream:
        return base64.b64encode(writer.write(bytes_stream)[1].getvalue() ).decode("utf-8")



# ------------------------  Table  ------------------------ #
if result:
    col_size =(1, 1, 1, 1, 1, 1, 2, 2, 1)
    colms = st.columns(col_size)
    fields = ["№", 'Создал', 'Дата', 'Номер документа', "Тип", "Статус"]
    for col, field_name in zip(colms, fields):
        col.write(field_name)

    for index, item in enumerate(result):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(col_size)
        file_path = os.getcwd() + '/tempDir/'+item['file_name']
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
            if st.button("Просмотреть документ", key=index+500):
                try:
                    with open(file_path, "rb") as file:
                        not_readed_data = item['not_readed_data']
                        base64_pdf = base64.b64encode(file.read()).decode("utf-8")
                        # base64_pdf = print_box_in_pdf(file_path, not_readed_data[0])
                        base64_pdf = print_box_in_pdf(file_path, not_readed_data)
                        file.close() 
                        components.html(f"""
                                    <html>
                                        <script> 
                                            var byteArray = new Uint8Array(atob("{base64_pdf}").split('').map(function(char) {{
                                                return char.charCodeAt(0);
                                            }}));
                                            var file = new Blob([byteArray], {{ type: 'application/pdf' }});
                                            var fileURL = URL.createObjectURL(file , {{type: 'application/pdf'}});
                                            window.open(fileURL);
                                        </script>
                                    </html>
                                """) 
                        
                except FileNotFoundError:
                    st.write("Не удалось найти файл")
        with col8:
            if st.button("Скачать PDF файл", key=index+500):
                try:
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
             if st.button("Проверить повторно", key=index+2000):
                try:
                    js_redirect("http://localhost:8501/?file_path="+str(file_path))
                except FileNotFoundError:
                    st.write("Не удалось найти файл")   

                        

            


        
                
            
if result and len(result) == 0:
    st.warning("Документы не найдены")
    
# st.write(result)
