# settings.py

from motor.motor_asyncio import AsyncIOMotorClient


# App host and port
HOST = 'localhost'
PORT = '8000'


# Mongo db params
DB = {
    'host': 'localhost',
    'port': 27017,
    'name': 'main'
}


def get_db(host="localhost", port=27017, name="main"):
    """ Connector to database (mongodb)

    :param name: (default main)
    :param host: (default localhost)
    :param port: (default 27017)
    :return: database

    """
    mongo_client = AsyncIOMotorClient(host, port)
    database = mongo_client[name]
    database.users.create_index(keys="username", unique=True)
    database.channels.create_index(keys="name", unique=True)
    return database


db = get_db(DB['host'], DB['port'], DB['name'])