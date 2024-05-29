from typing import TypedDict
import httpx
_address: str = None
_token: str = None

ID_FIELD_NAME = "id"


def read_address() -> str:
    if not _address:
        raise ValueError("Firestorm address was not configured")
    return _address + "get.php"


def write_address() -> str:
    if not _address:
        raise ValueError("Firestorm address was not configured")
    return _address + "post.php"


def file_address() -> str:
    if not _address:
        raise ValueError("Firestorm address was not configured")
    return _address + "files.php"


def write_token() -> str:
    if not _token:
        raise ValueError("Firestorm token was not configured")
    return _token


class WriteConfirmation(TypedDict):
    """Write status"""
    message: str


def extract_data(request: httpx.Response, is_json=True) -> list | dict:
    """Auto-extracts data from HTTPX request"""
    if is_json:
        res = request.json()
    else:
        # read binary
        res = request.content
    if request.status_code != httpx.codes.OK:
        raise ValueError(res)
    return res
