from typing import Literal, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")

CorePlatforms = Literal[
    "darwin",
    "linux",
    "windows",
]
