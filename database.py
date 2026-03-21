import mongoengine
import os

from dotenv import load_dotenv

load_dotenv()


MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME")


def connect_db():
    mongoengine.connect(host=MONGODB_URL, db=DB_NAME)


def disconnect_db():
    mongoengine.disconnect()