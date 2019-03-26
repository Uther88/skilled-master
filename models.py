# models.py

import settings
import motor.motor_asyncio
from dataclasses import dataclass, field
from aiohttp import log
import datetime
import json


client = motor.motor_asyncio.AsyncIOMotorClient(settings.DB['host'], settings.DB['port'])
db = client[settings.DB['name']]

db.users.create_index(keys="username", unique=True)
db.channels.create_index(keys="name", unique=True)



async def get_next_id(collection_name, step=1):
    result = await db.counters.find_one_and_update(
        filter={"_id": collection_name},
        update={"$inc": {"next": step}},
        upsert=True, new=True
    )
    return result["next"]


@dataclass(init=True)
class BaseModel:
    """ 
    The base class of the model that implements the data interface
    """

    _id: int

    # Get single object from db
    @classmethod
    async def get(cls, _id):
        data = await db[cls.Meta.collection].find_one({'_id': int(_id)})
        if data:
            obj = await cls(**data).prepare_related()
            return obj

    # Foreign key emulation
    async def prepare_related(self):
        for related_field in self.Meta.related_fields.keys():
            if getattr(self, related_field):
                setattr(
                    self,
                    related_field,
                    await self.Meta.related_fields[related_field].get(getattr(self, related_field))
                )
        return self

    # Get many objects with default limit = 100 and optional filtration
    @classmethod
    async def all(cls, limit=100, **kwargs):
        data = await db[cls.Meta.collection].find(kwargs).to_list(limit)
        return [await cls(**kw).prepare_related() for kw in data]

    # Create new object
    @classmethod
    async def create(cls, **kwargs):
        new_id = await get_next_id(cls.Meta.collection)
        kwargs['_id'] = new_id
        if cls.is_valid(kwargs):
            try:
                new_obj = cls(**kwargs)
                new = await db[cls.Meta.collection].insert_one(new_obj.__dict__)
                return cls.get(new.inserted_id)
            except Exception as e:
                await get_next_id(cls.Meta.collection, step=-1)
                log.web_logger.error(e)

    # Modify exists object
    @classmethod
    async def update(cls, _id, **kwargs):
        await db[cls.Meta.collection].update_one({'_id': _id}, {'$set': kwargs})
        return await cls.get(_id)

    # Delete object
    @classmethod
    async def delete(cls, **kwargs):
        await db[cls.Meta.collection].delete_one(kwargs)


    # Check for valid data
    @classmethod
    def is_valid(cls, data):
        try:
            cls(**data)
        except Exception as e:
            log.web_logger.error(e)
            return False
        else:
            return True

    # Convert model to dict
    def to_json(self):
        d = dict()
        for a, v in self.__dict__.items():
            if (hasattr(v, "to_json")):
                d[a] = v.to_json()
            else:
                d[a] = v
        return d

    @property
    def id(self):
        return self._id

    class Meta:
        collection = 'default'
        required_fields = []
        related_fields = {}


@dataclass
class Channel(BaseModel):
    name: str

    class Meta:
        collection = 'channels'
        required_fields = ['name']
        related_fields = {}


@dataclass
class User(BaseModel):
    username: str
    name: str
    surname: str
    patronymic: str
    position: dict
    channel: Channel
    coordinates: list = field(default_factory=lambda: [0, 0])
    percents: dict = field(default_factory=lambda: {'1': 30, '7000': 40, '15000': 50})
    is_staff: bool = False
    is_busy: bool = False
    is_active: bool = True
    avatar: str = None

    class Meta:
        collection = 'users'
        required_fields = ['username', 'name', 'surname', 'patronymic', 'position', 'channel']
        related_fields = {
            'channel': Channel
        }

    async def set_coordinates(self, coordinates):
        if type(coordinates) == list:
            await self.update(self.id, coordinates=coordinates)

    async def set_busy(self, busy):
        if type(busy) == bool:
            await self.update(self.id, is_busy=busy)


@dataclass
class Request(BaseModel):
    channel: Channel
    author: User
    master: User = None
    completed: dict = field(default_factory=lambda: {"is": False, "date": None})
    info: dict = field(default_factory=dict)
    denie: dict = field(default_factory=lambda: {"is": False, "who": None, "comment": None})
    finance: dict = field(
        default_factory=lambda: {"income": 0, "expense": 0, "total": 0, "percent": 0, "to_firm": 0, "to_master": 0})
    is_viewed: bool = False
    in_progress: bool = False
    date: str = datetime.datetime.now()

    class Meta:
        collection = 'requests'
        required_fields = ['channel', "info", "date"]
        related_fields = {
            'channel': Channel,
            'master': User,
            'author': User
        }


@dataclass
class Message(BaseModel):
    sender: User
    recipient: User
    text: str
    date: datetime.datetime = datetime.datetime.now()
    is_new: bool = True

    class Meta:
        collection = 'messages'
        required_fields = ['sender', 'recipient', 'text']
        related_fields = {
            'sender': User,
            'recipient': User,
        }
