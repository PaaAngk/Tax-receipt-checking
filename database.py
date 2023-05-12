import os
from deta import Deta  
from dotenv import load_dotenv 
import time

load_dotenv(".env")
DETA_KEY = os.getenv("DETA_KEY")

deta = Deta(DETA_KEY)

# This is how to create/connect a database
db_user = deta.Base("users_db")
db_doc = deta.Base("doc_db")


# --- User  ---
def insert_user(username, name, password):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db_user.put({"key": username, "name": name, "password": password})


def fetch_all_users():
    """Returns a dict of all users"""
    res = db_user.fetch()
    return res.items


def get_user(username):
    """If not found, the function will return None"""
    return db_user.get(username)


# --- Document  ---
def insert_document(doc_type, doc_number, doc_date, doc_create_date, doc_creater, file_name, status, not_readed_data):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db_doc.put({
        "doc_number": doc_number, 
        "doc_type": doc_type, 
        "doc_date": doc_date, 
        "doc_create_date": doc_create_date, 
        "doc_creater": doc_creater,
        "file_name" : file_name,
        "status": status,
        "not_readed_data": not_readed_data
    })


def fetch_all_document():
    """Returns a dict of all users"""
    res = db_doc.fetch()
    return res.items


def update_document(document, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db_doc.update(updates, document)


def delete_user(document):
    """Always returns None, even if the key does not exist"""
    return db_doc.delete(document)
    
# Find documents by Document number
def get_document_search_by_number(doc_number):
    first_fetch_res = db_doc.fetch([{"doc_number": doc_number}])
    return first_fetch_res.items

# Find documents by Document status
def get_avanc_report_by_status(status):
    first_fetch_res = db_doc.fetch([{"status": status, "doc_type": "Авансовый отчёт"} ])
    return first_fetch_res.items


# Find documents by needed document type and in range of date
def get_document_search_by_dateRange(doc_type, first_date, second_date):
    query = { "doc_date?gte": first_date, 
        "doc_date?lte": second_date }
    if doc_type != 'None':
        query["doc_type"] = doc_type

    first_fetch_res = db_doc.fetch([query])
    return first_fetch_res.items

