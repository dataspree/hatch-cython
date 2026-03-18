from hatch_cython.types import CorePlatforms, ListT, SetT

NORM_GLOB = r"([^\s]*)"
UAST = "${U_AST}"
EXIST_TRIM = 2
ANON = "anon"
INCLUDE = "include_"
OPTIMIZE = "-O2"
DIRECTIVES = {
    "binding": True,
    "language_level": 3,
}
LTPY311 = "python_version < '3.11'"
MUST_UNIQUE = ["-O", "-arch", "-march"]
POSIX_CORE: ListT[CorePlatforms] = ["darwin", "linux"]

precompiled_extensions: SetT[str] = {
    # py is left out as we have it optional / runtime value
    ".pyx",
    ".pxd",
}
intermediate_extensions: SetT[str] = {
    ".c",
    ".cpp",
}
_template_srcs: SetT[str] = {".py", ".pyi", *precompiled_extensions, *intermediate_extensions}
templated_extensions: SetT[str] = {f"{f}.in" for f in _template_srcs}
compiled_extensions: SetT[str] = {
    ".dll",
    # unix
    ".so",
    # windows
    ".pyd",
}
