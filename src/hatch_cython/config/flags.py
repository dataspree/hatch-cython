from collections.abc import Callable
from dataclasses import dataclass, field
from os import environ, pathsep
from typing import ClassVar, Optional

from hatch_cython.config.platform import PlatformArgs, parse_to_plat
from hatch_cython.types import DictT


@dataclass
class EnvFlag(PlatformArgs):
    env: str = field(default="")
    merges: bool = field(default=False)
    sep: str = field(default=" ")

    def __hash__(self) -> int:
        return hash(self.env)


__flags__ = (
    EnvFlag(env="CC", merges=False),
    EnvFlag(env="CPP", merges=False),
    EnvFlag(env="CXX", merges=False),
    EnvFlag(env="CFLAGS", merges=True),
    EnvFlag(env="CCSHARED", merges=True),
    EnvFlag(env="CPPFLAGS", merges=True),
    EnvFlag(env="LDFLAGS", merges=True),
    EnvFlag(env="LDSHARED", merges=True),
    EnvFlag(env="SHLIB_SUFFIX", merges=False),
    EnvFlag(env="AR", merges=False),
    EnvFlag(env="ARFLAGS", merges=True),
    EnvFlag(env="PATH", merges=True, sep=pathsep),
)


@dataclass
class EnvFlags:
    CC: Optional[PlatformArgs] = field(default=None)
    CPP: Optional[PlatformArgs] = field(default=None)
    CXX: Optional[PlatformArgs] = field(default=None)

    CFLAGS: Optional[PlatformArgs] = field(default=None)
    CCSHARED: Optional[PlatformArgs] = field(default=None)

    CPPFLAGS: Optional[PlatformArgs] = field(default=None)

    LDFLAGS: Optional[PlatformArgs] = field(default=None)
    LDSHARED: Optional[PlatformArgs] = field(default=None)

    SHLIB_SUFFIX: Optional[PlatformArgs] = field(default=None)

    AR: Optional[PlatformArgs] = field(default=None)
    ARFLAGS: Optional[PlatformArgs] = field(default=None)

    PATH: Optional[PlatformArgs] = field(default=None)

    custom: DictT[str, PlatformArgs] = field(default_factory=dict)
    env: dict = field(default_factory=environ.copy)

    __known__: ClassVar[DictT[str, EnvFlag]] = {e.env: e for e in __flags__}

    def __post_init__(self):
        for flag in __flags__:
            self.merge_to_env(flag, self.get_from_self)
        for flag in self.custom.values():
            self.merge_to_env(flag, self.get_from_custom)

    def merge_to_env(self, flag: EnvFlag, get: Callable[[str], Optional[EnvFlag]]):
        var = environ.get(flag.env)
        override: Optional[EnvFlag] = get(flag.env)
        if override and flag.merges:
            add = (var or "") + flag.sep
            self.env[flag.env] = add + override.arg  # type: ignore[operator]
        elif override:
            self.env[flag.env] = override.arg  # type: ignore[assignment]

    def get_from_self(self, attr):
        return getattr(self, attr)

    def get_from_custom(self, attr):
        return self.custom.get(attr)

    def masked_environ(self) -> dict:
        out = {}
        for k, v in self.env.items():
            if k not in self.__known__:
                out[k] = "*" * len(v)
            else:
                out[k] = v
        return out


def parse_env_args(
    kwargs: dict,
) -> EnvFlags:
    try:
        args: list = kwargs.pop("env")
        for i, arg in enumerate(args):
            parse_to_plat(EnvFlag, arg, args, i, require_argform=True)
    except KeyError:
        args = []
    kw: dict = {"custom": {}}
    for arg in args:
        if isinstance(arg, EnvFlag) and arg.applies():
            if arg.env in EnvFlags.__known__:
                kw[arg.env] = arg
            else:
                kw["custom"][arg.env] = arg
    envflags = EnvFlags(**kw)  # type: ignore[arg-type]
    return envflags
