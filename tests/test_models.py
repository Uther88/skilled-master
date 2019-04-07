# test_models.py

from unittest import TestCase
import asyncio
import logging
from time import time

from motor.motor_asyncio import AsyncIOMotorClient

from models import User, Channel, Request, Message

client = AsyncIOMotorClient()
db = client.test_db


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s : %(message)s')

errors = []
success = []


class ModelTestCase(TestCase):

    def __init__(self, model, model_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.model.Meta.db = db
        self.model_data = model_data
        self.longMessage = False

    async def start(self):
        logging.info(f'Start testing of { self.model.__name__ }')
        await self.test_create()
        await self.test_get()
        await self.test_to_json()
        logging.info(f'Ending testing of { self.model.__name__ } \n')

    async def test_create(self):
        obj = await self.model.create(**self.model_data)
        try:
            self.assertIsInstance(obj, self.model, msg=f"Create object of { self.model } - FAIL!")
        except Exception as e:
            logging.error(e)
            errors.append(1)
        else:
            logging.info(f'Testing for create model { self.model } - OK')
            success.append(1)
        self.obj = obj

    async def test_get(self):
        try:
            obj = await self.model.get(self.obj.id)
            self.assertEqual(obj, self.obj, msg=f"Get single obj of { self.model } - FAIL!")
        except Exception as e:
            logging.error(e)
            errors.append(1)
        else:
            logging.info(f'Testing for getting instance for model { self.model } - OK')
            success.append(1)

    async def test_to_json(self):
        try:
            json_data = self.obj.to_json()
            self.assertIsInstance(json_data, dict, msg=f"Conversion of { self.model } to json - FAIL!")
        except Exception as e:
            logging.error(e)
            errors.append(1)
        else:
            logging.info(f'Testing of converting to json { self.model} - OK')


user_data = dict(
        username="uter",
        password="password",
        name="Евгений",
        surname="Лихачев",
        patronymic="Сергеевич",
        position="master",
        channel=1
        )

channel_data = dict(name="test channel")

request_data = dict(
    author=1,
    channel=1,
    info={},
)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    start = time()

    loop.run_until_complete(ModelTestCase(User, user_data).start())
    loop.run_until_complete(ModelTestCase(Channel, channel_data).start())
    loop.run_until_complete(ModelTestCase(Request, request_data).start())

    client.drop_database('test_db')
    print(' ')
    logging.info('Complete! Testing time is %3.2f s. \n' % (time() - start))
    logging.info(f'Success tests - {len(success)}')
    logging.info(f'Failed tests - {len(errors)}')