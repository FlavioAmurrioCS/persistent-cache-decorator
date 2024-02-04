from __future__ import annotations

import datetime
import functools
from typing import Callable
from typing import overload
from typing import TypeVar

from persistent_cache.decorators import _CacheDuration
from persistent_cache.decorators import _PersistentCache
from persistent_cache.decorators import CacheBackendT
from persistent_cache.decorators import DEFAULT_CACHE_DURATION
from persistent_cache.decorators import SQLITE_CACHE_BACKEND
from typing_extensions import Concatenate
from typing_extensions import ParamSpec
from typing_extensions import Unpack

from typing_extensions import Self


Instance = TypeVar("Instance")
R = TypeVar("R")
P = ParamSpec("P")


class _PersistentPropertyCache(_PersistentCache[Concatenate[Instance, P], R, CacheBackendT]):
    @overload
    def __get__(self, instance: None, owner: type[Instance]) -> Self:
        # """Called when an attribute is accessed via class not an instance."""
        ...

    @overload
    def __get__(self, instance: Instance, owner: type[Instance]) -> Callable[P, R]:
        # """Called when an attribute is accessed on an instance variable."""
        ...

    def __get__(self, instance: Instance | None, owner: type[Instance]) -> Self | Callable[P, R]:
        if instance is None:
            return self
        return functools.partial(self.__call__, instance)  # type: ignore


# class _PersistentPropertyCache(Generic[Instance, P, R, CacheBackendT]):
#     __wrapped__: Callable[Concatenate[Instance, P], R]
#     __duration__: datetime.timedelta
#     __backend__: CacheBackendT
#     __persistent_cache__: _PersistentCache[Concatenate[Instance, P], R, CacheBackendT]

#     def __init__(
#         self,
#         func: Callable[Concatenate[Instance, P], R],
#         duration: datetime.timedelta,
#         backend: CacheBackendT,
#     ) -> None:
#         """Called on initialisation of descriptor."""
#         self.__wrapped__ = func
#         self.__duration__ = duration
#         self.__backend__ = backend

#         self.__persistent_cache__ = _PersistentCache(
#             self.__wrapped__, self.__duration__, self.__backend__
#         )
#         functools.update_wrapper(self, func)  # pyright: ignore[reportGeneralTypeIssues]

#     # def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
#     #     msg = "This function is only here for type checking"
#     #     raise NotImplementedError(msg)

#     @overload
#     def __get__(self, instance: None, owner: type[Instance]) -> Self:
#         # """Called when an attribute is accessed via class not an instance."""
#         ...

#     @overload
#     def __get__(self, instance: Instance, owner: type[Instance]) -> Callable[P, R]:
#         # """Called when an attribute is accessed on an instance variable."""
#         ...

#     def __get__(self, instance: Instance | None, owner: type[Instance]) -> Self | Callable[P, R]:
#         if instance is None:
#             return self
#         return functools.partial(self.__persistent_cache__.__call__, instance)  # type: ignore


def persistent_cached_property(
    *,
    backend: CacheBackendT = SQLITE_CACHE_BACKEND,  # type: ignore
    **duration: Unpack[_CacheDuration],
) -> Callable[
    [Callable[Concatenate[Instance, P], R]], _PersistentPropertyCache[Instance, P, R, CacheBackendT]
]:
    duration = duration or DEFAULT_CACHE_DURATION
    mcache_duration = datetime.timedelta(**duration)

    def inner(
        func: Callable[Concatenate[Instance, P], R],
    ) -> _PersistentPropertyCache[Instance, P, R, CacheBackendT]:
        return _PersistentPropertyCache(
            func=func,
            duration=mcache_duration,
            backend=backend,
        )

    return inner


class Foo:
    @persistent_cached_property(backend=SQLITE_CACHE_BACKEND, days=1)
    def bar(self, value: int) -> int:
        return value


foo = Foo()
foo.bar(3)

Foo.bar.cache_clear()

foo.bar(value=3)
