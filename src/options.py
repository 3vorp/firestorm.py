from dataclasses import dataclass
from typing import Any, List

@dataclass
class SearchOption:
    field: str
    criteria: str
    value: Any
    ignore_case: bool = False

@dataclass
class SelectOption:
    fields: List[str]

@dataclass
class ValueOption:
    field: str
    flatten: bool = False

@dataclass
class EditFieldOption:
    id: str | int
    field: str
    operation: str
    value: str = None