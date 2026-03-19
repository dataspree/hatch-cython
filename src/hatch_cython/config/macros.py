from typing import Optional

DefineMacros = list[tuple[str, Optional[str]]]


def parse_macros(define: list[list[str]]) -> DefineMacros:
    """Parses define_macros from list[list[str, ...]] -> list[tuple[str, str|None]]

    Args:
        define (ListT[ListT[str]]): list of listed strings of len 1 or 2. raises error if len > 2

    Raises:
        ValueError: length > 2 or types are not valid

    Returns:
        DefineMacros: list[tuple[str,str|None]]
    """
    for i, value in enumerate(define):
        inst = list(value) if isinstance(value, tuple) else value
        size = len(inst)
        if not (isinstance(inst, list) and size in (1, 2) and all(isinstance(v, str) or v is None for v in inst)):
            msg = "".join(
                f"define_macros[{i}]: macros must be defined as [name, <value>], "
                "where None value denotes #define FOO"
            )
            raise ValueError(msg, inst)
        if size == 1:
            define[i] = (inst[0], None)  # type: ignore[call-overload]
        else:
            define[i] = (inst[0], inst[1])  # type: ignore[call-overload]
    return define  # type: ignore[return-value]
