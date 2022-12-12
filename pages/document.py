import streamlit as st  # pip install streamlit
import database as db
import pandas as pd
import os


st.title("Document")
doc_type = st.selectbox("Choose document type", ["type1", "type2"])
doc_number = st.text_input("Document number")
doc_date = st.date_input("Document date")
submitted = st.button("search document")
result_items = []
if submitted:
    result = db.get_document_search( str(doc_number), str(doc_type), str(doc_date.strftime("%d-%m-%Y")))
    # st.write(result)
    
    if result:
        result_items = list(map(lambda x: x[1], list(result[0].items())))

        df_result = pd.DataFrame(
            [result_items], 
            columns=["doc_create_date","Creater","Document date","Document number","Type","file_name","key","Status"]
            ).drop(["doc_create_date", "file_name","key"],axis=1)
        st.dataframe(df_result)
        file_name = os.getcwd() + '/tempDir/'+result_items[5]
        with open(file_name, 'rb') as f:
            st.download_button('Download file', f, file_name='doc.pdf')
    else:
        st.warning("Documents is not found")
    




# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
<style>
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
# MainMenu {visibility: hidden;} 
