# utils.py

from secrets import token_urlsafe


def token_creator(func):

    """ Create token in api_keys collection on User creating """

    async def wrapped(*args, **kwargs):
        password = kwargs.pop('password')
        user = await func(*args, **kwargs)
        if user:
            token = token_urlsafe()
            api_key = user.Meta.db.api_keys.insert_one(
                dict(
                    user_id=user.id,
                    username=user.username,
                    password=password,
                    token=token
                )
            )
            return user
    return wrapped


def token_remover(func):

    """ Remove token and auth data from api_keys on User deleting """

    async def wrapped(*args, **kwargs):
        user = await func(*args, **kwargs)
        if user:
            result = await user.Meta.db.api_keys.delete_one({'user_id': user.id})
            return result
    return wrapped


async def get_next_id(cls, step=1, counters='counters'):
    """ Get next id

    Increase collections counter on creating object
    Counter will be decreased if step is negative

    :param cls: model class
    :param step: (default 1)
    :param counters: (default counters) counters collection name
    :return: next index or None

    """

    result = await cls.Meta.db[counters].find_one_and_update(
        filter={"_id": cls.Meta.collection},
        update={"$inc": {"next": step}},
        upsert=True, new=True
    )
    if step > 0:
        return result["next"]