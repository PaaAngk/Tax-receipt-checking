import os
from deta import Deta  
from dotenv import load_dotenv 


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


def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db_user.update(updates, username)


def delete_user(username):
    """Always returns None, even if the key does not exist"""
    return db_user.delete(username)



# --- Document  ---
def insert_document(doc_type, doc_number, doc_date, doc_create_date, doc_creater):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db_doc.put({"key": doc_number, "doc_type": doc_type, "doc_date": doc_date, "doc_create_date": doc_create_date, "doc_creater": doc_creater})


def fetch_all_document():
    """Returns a dict of all users"""
    res = db_doc.fetch()
    return res.items


def get_document(document):
    """If not found, the function will return None"""
    return db_doc.get(document)


def update_document(document, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db_doc.update(updates, document)


def delete_user(document):
    """Always returns None, even if the key does not exist"""
    return db_doc.delete(document)

