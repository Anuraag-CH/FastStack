import mongoengine
import os
from config import settings

def connect_db():
    mongoengine.connect(host=settings.MONGODB_URL, db=settings.DB_NAME)


def disconnect_db():
    mongoengine.disconnect()
