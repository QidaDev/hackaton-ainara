from pymongo import MongoClient


def get_db(uri):
    client = MongoClient(uri)
    return client
