from .internals import *
from .options import SearchOption, SelectOption, ValueOption, EditFieldOption
from dataclasses import asdict
from typing import Any, Callable
import httpx
import json


class Collection[T]:
    """Represents a Firestorm Collection"""
    collection_name: str

    @staticmethod
    def add_methods(el):
        return el

    def __init__(self, name: str):
        """Create a new Firestorm collection instance"""
        self.collection_name = name

    def add_method(self, method: Callable) -> Callable:
        """A decorator that registers additional methods and data to add to query results"""
        old_add_methods = self.add_methods

        def new_add_methods(el):
            old_output = old_add_methods(el)
            return method(old_output)

        self.add_methods = new_add_methods
        return method

    def __add_methods(self, el: list | dict, nested=True) -> Any:
        """Add user methods to returned data"""
        # can't add properties on falsy values
        if not el:
            return el
        if isinstance(el, list):
            return list(map(self.add_methods, el))
        # nested objects
        if nested and isinstance(el, object):
            for k in el.keys():
                el[k] = self.add_methods(el[k])
            return el

        # add directly to single object
        return self.add_methods(el)

    def __get_request(self, command: str, data: dict = {}, object_like=True) -> Any:
        """Send GET request with provided data and return extracted response"""
        obj = {
            "collection": self.collection_name,
            "command": command,
            **data,
        }

        request = httpx.request(
            method="GET",
            url=read_address(),
            json=obj
        )

        res = extract_data(request)

        # reject php error strings if enforcing return type
        if object_like and (not isinstance(res, dict) and not isinstance(res, list)):
            raise ValueError(res)
        return res

    def __write_data(self, command: str, value: Any = None, multiple=False) -> dict:
        """Generate POST data with provided data"""
        obj = {
            "token": write_token(),
            "collection": self.collection_name,
            "command": command
        }

        if value:
            value = json.loads(json.dumps(value))

        if multiple and isinstance(value, list):
            for v in value:
                if isinstance(v, dict) and ID_FIELD_NAME in v:
                    del v[ID_FIELD_NAME]
        elif multiple == False and isinstance(value, dict) and ID_FIELD_NAME in value:
            del value[ID_FIELD_NAME]

        if value:
            if multiple:
                obj["values"] = value
            else:
                obj["value"] = value

        return obj

    def sha1(self) -> str:
        """Get the sha1 hash of the JSON
        - Can be used to compare file content without downloading the file
        """
        # string value is correct so we don't need validation
        return self.__get_request("sha1", {}, False)

    def get(self, key: str | int) -> T:
        """Get an element from the collection by its key"""
        res = self.__get_request("get", {
            "id": key
        })

        first_key = list(res.keys())[0]
        res[first_key][ID_FIELD_NAME] = first_key
        res = res[first_key]
        return self.__add_methods(res, False)

    def search_keys(self, keys: list[str]) -> list[T]:
        """Get multiple elements from the collection by their keys"""
        if not isinstance(keys, list):
            raise TypeError("Incorrect keys")

        res = self.__get_request("searchKeys", {"search": keys})
        out = []
        for id, value in res.items():
            value[ID_FIELD_NAME] = id
            out.append(value)

        return self.__add_methods(out)

    def search(self, options: list[SearchOption], random=False) -> list[T]:
        """Search through the collection"""
        if not isinstance(options, list):
            raise TypeError("search_options should be an list")

        dict_options = []
        for option in options:
            if (
                option.field is None
                or option.criteria is None
                or option.value is None
            ):
                raise TypeError("Missing fields in options list")

            if not isinstance(option.field, str):
                raise TypeError(
                    f"{json.dumps(option)} search option field is not a string")

            if option.criteria == "in" and not isinstance(option.value, list):
                raise TypeError("in takes a list of values")

            # TODO: add more strict value field warnings in JS and PHP

            dict_option = asdict(option)
            if "ignore_case" in dict_option:
                # convert to camelCase
                dict_option["ignoreCase"] = dict_option["ignore_case"]
                del dict_option["ignore_case"]
            dict_options.append(dict_option)

        params = {
            "search": dict_options
        }

        if random != False:
            if random == True:
                params["random"] = {}
            else:
                try:
                    seed = int(random)
                except ValueError:
                    raise TypeError(
                        "random takes as parameter True, False or an integer value")
                params.random = {"seed": seed}

        res = self.__get_request("search", params)
        out = []
        for id, value in res.items():
            value[ID_FIELD_NAME] = id
            out.append(value)

        return self.__add_methods(out)

    def read_raw(self, original=False) -> dict[str, T]:
        """Read the entire collection"""
        data = self.__get_request("read_raw")

        if original:
            return data

        for key in data.keys():
            data[key][ID_FIELD_NAME] = key

        return self.__add_methods(data)

    def select(self, option: SelectOption = {}) -> dict[str, T]:
        """Get only selected fields from the collection
        - Essentially an upgraded version of `read_raw`
        """
        data = self.__get_request("select", {
            "select": asdict(option)
        })

        for key in data.keys():
            data[key][ID_FIELD_NAME] = key

        return self.__add_methods(data)

    def values(self, option: ValueOption) -> list[T]:
        """Get all distinct non-null values for a given key across a collection"""
        res = self.__get_request("values", {"values": asdict(option)})

        data = []
        for d in res.values():
            if d is not None:
                data.append(d)

        return data

    def random(self, max: int = None, seed: int = None, offset: int = None) -> list[T]:
        """Read random elements of the collection"""
        params = {}
        if max is not None:
            if not isinstance(max, int) or max < -1:
                raise TypeError("Expected integer >= -1 for the max")
            params["max"] = max

        has_seed = seed is not None
        has_offset = offset is not None

        if has_seed and not has_offset:
            raise TypeError("You can't put an offset without a seed")

        if has_offset and (not isinstance(offset, int) or offset < 0):
            raise TypeError("Expected integer >= -1 for the max")

        if has_seed:
            if not isinstance(seed, int):
                raise TypeError("Expected integer for the seed")

            if not has_offset:
                offset = 0

            params["seed"] = seed
            params["offset"] = offset

        data = self.__get_request("random", {"random": params})

        for key in data.keys():
            data[key][ID_FIELD_NAME] = key

        return self.__add_methods(data)

    def write_raw(self, value: dict[str, T]) -> WriteConfirmation:
        """Set the entire content of the collection
        - Only use this method if you know what you are doing!
        """
        return extract_data(httpx.post(
            write_address(), json=self.__write_data("write_raw", value),
        ))

    def add(self, value: T) -> str:
        """Append a value to the collection
        - Only works if autoKey is enabled server-side
        """
        res = extract_data(httpx.post(
            write_address(), json=self.__write_data("add", value)))

        if not isinstance(res, dict) or "id" not in res or not isinstance(res.id, str):
            raise ValueError(res)

        return res.id

    def add_bulk(self, values: list[T]) -> str:
        """Append multiple values to the collection
        - Only works if autoKey is enabled server-side
        """
        res = extract_data(httpx.post(
            write_address(), json=self.__write_data("addBulk", values, True)
        ))

        return res.ids

    def remove(self, key: str | int) -> WriteConfirmation:
        """Remove an element from the collection by its key"""
        return extract_data(httpx.post(write_address(), json=self.__write_data("remove", key)))

    def remove_bulk(self, keys: list[str | int]) -> WriteConfirmation:
        """Remove multiple elements from the collection by their keys"""
        return extract_data(httpx.post(write_address(), json=self.__write_data("removeBulk", keys)))

    def set(self, key: str, value: T) -> WriteConfirmation:
        """Set a value in the collection by key"""
        data = self.__write_data("set", value)
        data["key"] = key
        return extract_data(httpx.post(write_address(), json=data))

    def set_bulk(self, keys: list[str | int], values: list[T]) -> WriteConfirmation:
        """Set multiple values in the collection by their keys"""
        data = self.__write_data("setBulk", values, True)
        data["keys"] = keys
        return extract_data(httpx.post(write_address(), json=data))

    def edit_field(self, option: EditFieldOption) -> WriteConfirmation:
        """Edit an element's field in the collection"""
        data = self.__write_data("editField", asdict(option), None)
        return extract_data(httpx.post(write_address(), json=data))

    def edit_field_bulk(self, options: list[EditFieldOption]) -> WriteConfirmation:
        """Edit multiple elements' fields in the collection"""
        data = self.__write_data("editFieldBulk", list(map(asdict, options)), None)
        return extract_data(httpx.post(write_address(), json=data))
