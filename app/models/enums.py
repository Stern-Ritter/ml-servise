from enum import Enum


class RoleName(str, Enum):
    USER = 'user'
    ADMIN = 'admin'


class Currency(str, Enum):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'


class TransactionType(str, Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'


class PredictStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
