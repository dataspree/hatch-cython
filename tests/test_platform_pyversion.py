from typing import Callable, Optional, Union

from hatch_cython.types import P


# basic test to assert we can use subscriptable generics
def test_type_compat():
    tuple[int, str]
    dict[str, str]
    list[str]
    Callable[P, str]  # type: ignore[type-arg]
    Union[str, None]
    Optional[str]
