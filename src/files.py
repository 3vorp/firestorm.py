"""Firestorm file handler"""

from .internals import *
from typing import Any
import httpx


def get(path: str) -> bytes:
    """Get a file by its path"""
    data = {
        "path": path
    }
    return extract_data(
        httpx.request(method="GET", url=file_address(), params=data),
        # read binary
        False
    )


def upload(*, path: str, file: Any, overwrite=False) -> WriteConfirmation:
    """Upload a file"""
    data = {
        "path": path,
        "overwrite": overwrite,
        "token": write_token()
    }

    files = {
        "file": file,
    }

    return extract_data(
        # multipart/form-data files are treated separately from other data in httpx
        httpx.post(file_address(), data=data, files=files)
    )


def delete(path: str) -> WriteConfirmation:
    """Delete a file by its path"""
    obj = {
        "path": path,
        "token": write_token()
    }
    return extract_data(
        httpx.delete(file_address(), json=obj)
    )
