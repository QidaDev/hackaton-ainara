from pymongo import MongoClient

# Set by create_app(); used by MongoModel for persistence
db = None


def get_db(uri):
    client = MongoClient(uri)
    return client
