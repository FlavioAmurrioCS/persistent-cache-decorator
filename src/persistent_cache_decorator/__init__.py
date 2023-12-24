from __future__ import annotations

import datetime
import functools
import os
from typing import Any
from typing import Callable
from typing import Generic

from persistent_cache_decorator.backend.json import JsonCacheBackend
from persistent_cache_decorator.backend.pickle import PickleCacheBackend
from persistent_cache_decorator.backend.sqlite import SqliteCacheBackend
from typing_extensions import ParamSpec
from typing_extensions import Protocol
from typing_extensions import TypedDict
from typing_extensions import TypeVar

_R = TypeVar('_R')
_P = ParamSpec('_P')

_DEFAULT_CACHE_LOCATION = os.path.expanduser('~/.cache/persistent_cache')


class _cache_duration(TypedDict, total=False):
    days: float
    seconds: float
    microseconds: float
    milliseconds: float
    minutes: float
    hours: float
    weeks: float


class CacheBackend(Protocol, Generic[_R]):
    def __init__(self, filename: str) -> None:
        ...

    def __save__(self) -> str:
        ...

    def get_cached_results(self, *, func: Callable[..., _R], args: tuple[Any, ...], kwargs: dict[str, Any], lifespan: datetime.timedelta) -> _R:
        ...

    def del_function_cache(self, *, func: Callable[..., _R]) -> None:
        ...


class _persistent_cache(Generic[_P, _R]):
    __wrapped__: Callable[_P, _R]
    __duration__: datetime.timedelta
    __backend__: CacheBackend[_R]

    def __init__(
        self,
        func: Callable[_P, _R],
        duration: datetime.timedelta,
        backend: CacheBackend[_R],
    ) -> None:
        self.__wrapped__ = func
        self.__duration__ = duration
        self.__backend__ = backend
        functools.update_wrapper(self, func)

    def cache_clear(self) -> None:
        self.__backend__.del_function_cache(func=self.__wrapped__)

    def no_cache_call(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        return self.__wrapped__(*args, **kwargs)

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        if 'NO_CACHE' in os.environ:
            return self.no_cache_call(*args, **kwargs)
        os.makedirs(_DEFAULT_CACHE_LOCATION, exist_ok=True)
        if 'BUST_CACHE' in os.environ:
            self.cache_clear()
        return self.__backend__.get_cached_results(
            func=self.__wrapped__,
            args=args,
            kwargs=kwargs,
            lifespan=self.__duration__,
        )


JSON_CACHE_BACKEND: CacheBackend[Any] = JsonCacheBackend(
    filename=os.path.join(_DEFAULT_CACHE_LOCATION, 'data.json'),
)
PICKLE_CACHE_BACKEND: CacheBackend[Any] = PickleCacheBackend(
    filename=os.path.join(_DEFAULT_CACHE_LOCATION, 'data.pickle'),
)
SQLITE_CACHE_BACKEND: CacheBackend[Any] = SqliteCacheBackend(
    filename=os.path.join(_DEFAULT_CACHE_LOCATION, 'data.sqlite'),
)


def persistent_cache(
    *,
    duration: _cache_duration | None = None,
    backend: CacheBackend[_R] = SQLITE_CACHE_BACKEND,
) -> Callable[[Callable[_P, _R]], _persistent_cache[_P, _R]]:
    mcache_duration = datetime.timedelta(**(duration or {'days': 1}))

    def inner(func: Callable[_P, _R]) -> _persistent_cache[_P, _R]:
        return _persistent_cache(
            func=func,
            duration=mcache_duration,
            backend=backend,
        )
    return inner
