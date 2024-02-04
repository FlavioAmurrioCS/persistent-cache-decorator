from __future__ import annotations

import datetime
import functools
import os
from typing import Any
from typing import Callable
from typing import Generic

from persistent_cache.backend.json import JsonCacheBackend
from persistent_cache.backend.pickle import PickleCacheBackend
from persistent_cache.backend.sqlite import SqliteCacheBackend
from typing_extensions import ParamSpec
from typing_extensions import Protocol
from typing_extensions import TypedDict
from typing_extensions import TypeVar
from typing_extensions import Unpack

_R = TypeVar("_R")
_P = ParamSpec("_P")

_DEFAULT_CACHE_LOCATION = os.path.expanduser("~/.cache/persistent_cache")


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


class CacheBackend(Protocol):
    """Interface for cache backends used by the persistent cache decorator."""

    def get_cached_results(
        self,
        *,
        func: Callable[..., _R],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        lifespan: datetime.timedelta,
    ) -> _R:
        """
        Retrieve the cached results for a function call.

        Args:
        ----
            func (Callable[..., _R]): The function to retrieve cached results for.
            args (tuple[Any, ...]): The positional arguments passed to the function.
            kwargs (dict[str, Any]): The keyword arguments passed to the function.
            lifespan (datetime.timedelta): The maximum age of the cached results.

        Returns:
        -------
            _R: The cached results, if available.
        """
        ...  # no cov

    def del_function_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Delete the cache for a specific function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cache for.
        """
        ...  # no cov


CacheBackendT = TypeVar("CacheBackendT", bound=CacheBackend)


class _PersistentCache(Generic[_P, _R, CacheBackendT]):
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
    __backend__: CacheBackendT

    def __init__(
        self,
        func: Callable[_P, _R],
        duration: datetime.timedelta,
        backend: CacheBackendT,
    ) -> None:
        self.__wrapped__ = func
        self.__duration__ = duration
        self.__backend__ = backend
        functools.update_wrapper(self, func)

    def cache_clear(self) -> None:
        """Clears the cache for the wrapped function."""
        self.__backend__.del_function_cache(func=self.__wrapped__)

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
            return self.no_cache_call(*args, **kwargs)
        os.makedirs(_DEFAULT_CACHE_LOCATION, exist_ok=True)
        return self.__backend__.get_cached_results(
            func=self.__wrapped__,
            args=args,
            kwargs=kwargs,
            lifespan=self.__duration__,
        )

    def __set_name__(self, owner: Any, name: str) -> Any:  # noqa: ANN401
        self.__wrapped__.__name__ = name

    def __get__(self, instance: Any, owner: Any) -> Any:  # noqa: ANN401
        if owner is None:
            return self
        return functools.partial(self.__call__, instance)


JSON_CACHE_BACKEND = JsonCacheBackend(filename=os.path.join(_DEFAULT_CACHE_LOCATION, "data.json"))
PICKLE_CACHE_BACKEND = PickleCacheBackend(
    filename=os.path.join(_DEFAULT_CACHE_LOCATION, "data.pickle")
)
SQLITE_CACHE_BACKEND = SqliteCacheBackend(
    filename=os.path.join(_DEFAULT_CACHE_LOCATION, "data.sqlite")
)
DEFAULT_CACHE_DURATION: _CacheDuration = {"days": 1}


def persistent_cache(
    *,
    backend: CacheBackendT = SQLITE_CACHE_BACKEND,  # type: ignore
    **duration: Unpack[_CacheDuration],
) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, CacheBackendT]]:
    """
    Decorator that adds persistent caching functionality to a function.

    Args:
    ----
        duration: The duration for which the cache should be valid. Default is 1 day.
        backend: The cache backend to use. Default is SQLITE_CACHE_BACKEND.

    Returns:
    -------
        A decorator that can be applied to a function to enable persistent caching.
    """
    duration = duration or DEFAULT_CACHE_DURATION
    mcache_duration = datetime.timedelta(**duration)

    def inner(func: Callable[_P, _R]) -> _PersistentCache[_P, _R, CacheBackendT]:
        return _PersistentCache(
            func=func,
            duration=mcache_duration,
            backend=backend,
        )

    return inner


def json_cache(
    **duration: Unpack[_CacheDuration],
) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, JsonCacheBackend]]:
    """
    Decorator that caches the result of a function using a JSON cache backend.

    Args:
    ----
        duration: The duration for which the cache should be valid. Defaults to 1 day.

    Returns:
    -------
        A decorator that can be used to cache the result of a function.
    """
    return persistent_cache(
        backend=JSON_CACHE_BACKEND,
        **duration,
    )


def pickle_cache(
    **duration: Unpack[_CacheDuration],
) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, PickleCacheBackend]]:
    """
    Decorator that caches the result of a function using pickle serialization.

    Args:
    ----
        duration: The duration for which the cache should be valid. Default is 1 day.

    Returns:
    -------
        A decorator that can be applied to a function to enable caching.
    """
    return persistent_cache(
        backend=PICKLE_CACHE_BACKEND,
        **duration,
    )


def sqlite_cache(
    **duration: Unpack[_CacheDuration],
) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, SqliteCacheBackend]]:
    """
    Decorator that enables caching of function results using SQLite as the cache backend.

    Args:
    ----
        duration: The duration for which the cache should be valid. Defaults to 1 day.

    Returns:
    -------
        A decorator that can be applied to functions to enable caching.

    """
    return persistent_cache(
        backend=SQLITE_CACHE_BACKEND,
        **duration,
    )


def cache_decorator_factory(  # noqa: D417
    *,
    backend: CacheBackendT,
    **default_duration: Unpack[_CacheDuration],
) -> Callable[..., Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, CacheBackendT]]]:
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
    ) -> Callable[[Callable[_P, _R]], _PersistentCache[_P, _R, CacheBackendT]]:
        return persistent_cache(
            backend=backend,
            **(duration or default_duration),
        )

    return _inner_
