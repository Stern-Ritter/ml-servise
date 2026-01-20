from enum import Enum


class RoleName(str, Enum):
    USER = 'user'
    ADMIN = 'admin'
