from __future__ import annotations

import datetime
import functools
import inspect
import os
from pathlib import Path
from typing import Callable
from typing import Generic
from typing import overload
from typing import TYPE_CHECKING

from persistent_cache.backend import CacheBackend
from persistent_cache.backend.json import JsonCacheBackend
from persistent_cache.backend.pickle import PickleCacheBackend
from persistent_cache.backend.sqlite import SqliteCacheBackend
from typing_extensions import Concatenate
from typing_extensions import ParamSpec
from typing_extensions import Protocol
from typing_extensions import Self
from typing_extensions import TypedDict
from typing_extensions import TypeVar
from typing_extensions import Unpack


if TYPE_CHECKING:

    class _CacheDuration(TypedDict, total=False):
        """
        Represents the duration of cache expiration.

        Attributes
        ----------
            days (float): Number of days.
            seconds (float): Number of seconds.
            microseconds (float): Number of microseconds.
            milliseconds (float): Number of milliseconds.
            minutes (float): Number of minutes.
            hours (float): Number of hours.
            weeks (float): Number of weeks.

        """

        days: float
        seconds: float
        microseconds: float
        milliseconds: float
        minutes: float
        hours: float
        weeks: float

    _R_co = TypeVar("_R_co", covariant=True)

    class _PersistentCacheCallable(Protocol[_R_co]):
        def __call__(self, **duration: Unpack[_CacheDuration]) -> _R_co: ...


DEFAULT_CACHE_LOCATION = Path("~/.cache/persistent_cache").expanduser()

_P = ParamSpec("_P")
_R = TypeVar("_R")
_CacheBackendT = TypeVar("_CacheBackendT", bound=CacheBackend)


class _PersistentCache(Generic[_P, _R, _CacheBackendT]):
    """
    A decorator class that provides persistent caching functionality for a function.

    Args:
    ----
        func (Callable[_P, _R]): The function to be decorated.
        duration (datetime.timedelta): The duration for which the cached results should be considered valid.
        backend (_backend): The backend storage for the cached results.

    Attributes:
    ----------
        __wrapped__ (Callable[_P, _R]): The wrapped function.
        __duration__ (datetime.timedelta): The duration for which the cached results should be considered valid.
        __backend__ (_backend): The backend storage for the cached results.

    """  # noqa: E501

    __wrapped__: Callable[_P, _R]
    __duration__: datetime.timedelta
    __backend__: _CacheBackendT

    def __init__(
        self,
        func: Callable[_P, _R],
        duration: datetime.timedelta,
        backend: _CacheBackendT,
    ) -> None:
        self.__wrapped__ = func
        self.__duration__ = duration
        self.__backend__ = backend
        functools.update_wrapper(self, func)

    def cache_clear(self) -> None:
        """Clears the cache for the wrapped function."""
        self.__backend__.del_func_cache(func=self.__wrapped__)

    def no_cache_call(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """
        Calls the wrapped function without using the cache.

        Args:
        ----
            *args (_P.args): Positional arguments for the wrapped function.
            **kwargs (_P.kwargs): Keyword arguments for the wrapped function.

        Returns:
        -------
            _R: The result of the wrapped function.

        """
        return self.__wrapped__(*args, **kwargs)

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """
        Calls the wrapped function, either using the cache or bypassing it based on environment variables.

        Args:
        ----
            *args (_P.args): Positional arguments for the wrapped function.
            **kwargs (_P.kwargs): Keyword arguments for the wrapped function.

        Returns:
        -------
            _R: The result of the wrapped function.

        """  # noqa: E501
        if "NO_CACHE" in os.environ:
            return self.__wrapped__(*args, **kwargs)

        os.makedirs(DEFAULT_CACHE_LOCATION, exist_ok=True)

        if not inspect.iscoroutinefunction(self.__wrapped__):
            return self.__backend__.get_cache_or_call(
                func=self.__wrapped__,
                args=args,
                kwargs=kwargs,
                lifespan=self.__duration__,
            )

        return self.__backend__.get_cache_or_call_async(  # type: ignore[return-value]
            func=self.__wrapped__,
            args=args,
            kwargs=kwargs,
            lifespan=self.__duration__,
        )


CACHE_BACKEND_JSON: CacheBackend = JsonCacheBackend(
    DEFAULT_CACHE_LOCATION.joinpath("data.json").as_posix()
)
CACHE_BACKEND_PICKLE: CacheBackend = PickleCacheBackend(
    DEFAULT_CACHE_LOCATION.joinpath("data.pickle").as_posix()
)
CACHE_BACKEND_SQLITE: CacheBackend = SqliteCacheBackend(
    DEFAULT_CACHE_LOCATION.joinpath("data.sqlite").as_posix()
)
DEFAULT_CACHE_DURATION: _CacheDuration = {"days": 1}


def persistent_cache(
    *,
    backend: _CacheBackendT = CACHE_BACKEND_SQLITE,  # type: ignore[assignment]
    **duration: Unpack[_CacheDuration],
) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, _CacheBackendT]]:
    """
    Decorator that adds persistent caching functionality to a function.

    Args:
    ----
        duration: The duration for which the cache should be valid. Default is 1 day.
        backend: The cache backend to use. Default is CACHE_BACKEND_SQLITE.

    Returns:
    -------
        A decorator that can be applied to a function to enable persistent caching.

    """
    duration = duration or DEFAULT_CACHE_DURATION
    mcache_duration = datetime.timedelta(**duration)

    def inner(func: Callable[_P, _R]) -> _PersistentCache[_P, _R, _CacheBackendT]:
        return _PersistentCache(
            func=func,
            duration=mcache_duration,
            backend=backend,
        )

    return inner


def cache_decorator_factory(  # noqa: D417
    *,
    backend: _CacheBackendT,
    **default_duration: Unpack[_CacheDuration],
) -> _PersistentCacheCallable[
    Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, _CacheBackendT]]
]:
    """
    A factory function that returns a decorator that can be used to cache the result of a function.

    Args:
    ----
        backend: The cache backend to use.
        duration: The duration for which the cache should be valid. Default is 1 day.

    Returns:
    -------
        A decorator that can be applied to a function to enable persistent caching.

    """

    def _inner_(
        **duration: Unpack[_CacheDuration],
    ) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, _CacheBackendT]]:
        """
        Decorator that enables caching of function results using _CacheBackendT as the cache backend.

        Args:
        ----
            duration: The duration for which the cache should be valid. Defaults to 1 day.

        Returns:
        -------
            A decorator that can be applied to functions to enable caching.

        """  # noqa: E501
        return persistent_cache(
            backend=backend,
            **(duration or default_duration),
        )

    _inner_.__name__ = persistent_cache.__name__

    return _inner_


json_cache = cache_decorator_factory(backend=CACHE_BACKEND_JSON)
pickle_cache = cache_decorator_factory(backend=CACHE_BACKEND_PICKLE)
sqlite_cache = cache_decorator_factory(backend=CACHE_BACKEND_SQLITE)


####################################################################################################

Instance = TypeVar("Instance")


class _PersistentCachedProperty(_PersistentCache[Concatenate[Instance, _P], _R, _CacheBackendT]):
    @overload
    def __get__(self, instance: None, owner: type[Instance]) -> Self: ...

    @overload
    def __get__(self, instance: Instance, owner: type[Instance]) -> Callable[_P, _R]: ...

    def __get__(self, instance: Instance | None, owner: type[Instance]) -> Self | Callable[_P, _R]:
        if instance is None:
            return self
        return functools.partial(self.__call__, instance)  # pyright: ignore[reportReturnType]


def persistent_cached_property(
    *,
    backend: _CacheBackendT = CACHE_BACKEND_SQLITE,  # type: ignore[assignment]
    **duration: Unpack[_CacheDuration],
) -> Callable[
    [Callable[Concatenate[Instance, _P], _R]],
    _PersistentCachedProperty[Instance, _P, _R, _CacheBackendT],
]:
    """
    Decorator that adds persistent caching functionality to a function.

    Args:
    ----
        backend: The cache backend to use. Defaults to CACHE_BACKEND_SQLITE.
        duration: The duration of the cache. Accepts keyword arguments for days, hours, minutes, seconds, microseconds.

    Returns:
    -------
        A callable that can be used as a decorator to create a persistent cached property.

    """  # noqa: E501
    duration = duration or DEFAULT_CACHE_DURATION
    mcache_duration = datetime.timedelta(**duration)

    def inner(
        func: Callable[Concatenate[Instance, _P], _R],
    ) -> _PersistentCachedProperty[Instance, _P, _R, _CacheBackendT]:
        return _PersistentCachedProperty(
            func=func,
            duration=mcache_duration,
            backend=backend,
        )

    return inner


def cached_property_decorator_factory(
    *,
    backend: _CacheBackendT,
    **default_duration: Unpack[_CacheDuration],
) -> _PersistentCacheCallable[
    Callable[
        [Callable[Concatenate[Instance, _P], _R]],
        _PersistentCachedProperty[Instance, _P, _R, _CacheBackendT],
    ]
]:
    def _inner_(
        **duration: Unpack[_CacheDuration],
    ) -> Callable[
        [Callable[Concatenate[Instance, _P], _R]],
        _PersistentCachedProperty[Instance, _P, _R, _CacheBackendT],
    ]:
        return persistent_cached_property(
            backend=backend,
            **(duration or default_duration),
        )

    _inner_.__name__ = persistent_cached_property.__name__
    return _inner_


json_cached_property = cached_property_decorator_factory(backend=CACHE_BACKEND_JSON)
pickle_cached_property = cached_property_decorator_factory(backend=CACHE_BACKEND_PICKLE)
sqlite_cached_property = cached_property_decorator_factory(backend=CACHE_BACKEND_SQLITE)
