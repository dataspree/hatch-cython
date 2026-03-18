from typing import Literal, ParamSpec, TypeAlias, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

TupleT: TypeAlias = tuple
DictT: TypeAlias = dict
ListT: TypeAlias = list
SetT: TypeAlias = set

ListStr = list[str]
CorePlatforms = Literal[
    "darwin",
    "linux",
    "windows",
]
