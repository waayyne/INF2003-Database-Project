import os
import mysql.connector
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


def get_mariadb_connection():
    return mysql.connector.connect(
        host=os.getenv("MARIADB_HOST"),
        user=os.getenv("MARIADB_USER"),
        password=os.getenv("MARIADB_PASSWORD"),
        database=os.getenv("MARIADB_DATABASE")
    )


def get_mongo_collection():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DATABASE")]
    return db[os.getenv("MONGO_REVIEWS_COLLECTION")]