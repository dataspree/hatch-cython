from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Autoimport:
    pkg: str

    include: str
    libraries: Optional[str] = field(default=None)
    library_dirs: Optional[str] = field(default=None)
    required_call: Optional[str] = field(default=None)


__packages__ = {
    a.pkg: a
    for a in (
        Autoimport("numpy", "get_include"),
        Autoimport(
            "pyarrow",
            include="get_include",
            libraries="get_libraries",
            library_dirs="get_library_dirs",
            required_call="create_library_symlinks",
        ),
        Autoimport("pythran", "get_include"),
    )
}
