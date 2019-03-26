# routes.py

import handlers


routes = [
    ('GET', '/', handlers.index_handler),
    ('GET', '/auth', handlers.auth_handler),
]