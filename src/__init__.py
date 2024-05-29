"""Self hosted Firestore-like database with API endpoints based on micro bulk operations"""

# export internals, files, and options directly
from . import internals
from . import files
from .options import *
from .Collection import Collection


def address(new_value: str = None) -> str:
    if not new_value:
        return internals.read_address()
    if not new_value.endswith("/"):
        new_value += "/"
    if new_value:
        internals._address = new_value
    return internals._address


def token(new_value: str = None) -> str:
    if not new_value:
        return internals.write_token()
    if new_value:
        internals._token = new_value
    return internals._token


def collection[T](name: str) -> Collection[T]:
    return Collection[T](name)


ID_FIELD = internals.ID_FIELD_NAME
