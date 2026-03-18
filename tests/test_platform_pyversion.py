from typing import Callable, Optional, Union

from hatch_cython.types import DictT, ListT, P, TupleT


# basic test to assert we can use subscriptable generics
def test_type_compat():
    TupleT[int, str]  # type: ignore[type-arg]
    DictT[str, str]
    ListT[str]
    Callable[P, str]  # type: ignore[type-arg]
    Union[str, None]
    Optional[str]
