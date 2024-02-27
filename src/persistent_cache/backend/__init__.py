from __future__ import annotations

import datetime
import inspect
import os
from typing import Any
from typing import Callable

from typing_extensions import ParamSpec
from typing_extensions import Protocol
from typing_extensions import TypeVar


_P = ParamSpec("_P")
_KEY_T = TypeVar("_KEY_T")
_STORE_T = TypeVar("_STORE_T")


def get_function_identifier(func: Callable[_P, Any]) -> str:
    module = inspect.getmodule(func)
    return f"{module.__name__ if module else ''}.{func.__qualname__}"


class CacheBackend(Protocol):
    """Interface for cache backends used by the persistent cache decorator."""

    def get_cache_or_call(
        self,
        *,
        func: Callable[_P, Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        lifespan: datetime.timedelta,
    ) -> Any:  # noqa: ANN401
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

    def del_func_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Delete the cache for a specific function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cache for.

        """
        ...  # no cov


class AbstractCacheBackend(CacheBackend, Protocol[_KEY_T, _STORE_T]):
    """Interface for cache backends used by the persistent cache decorator."""

    def hash_key(
        self,
        *,
        func: Callable[_P, Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> tuple[str, _KEY_T]:
        return get_function_identifier(func), f"args: {args}, kwargs: {kwargs}"  # type: ignore

    def get(self, *, key: tuple[str, _KEY_T]) -> tuple[datetime.datetime, _STORE_T] | None:
        ...

    def delete(self, *, key: tuple[str, _KEY_T]) -> None:
        ...

    def put(self, *, key: tuple[str, _KEY_T], data: _STORE_T) -> None:
        ...

    def decode(self, *, data: _STORE_T) -> Any:  # noqa: ANN401
        return data

    def encode(self, *, data: Any) -> _STORE_T:  # noqa: ANN401
        return data

    def get_cache_or_call(
        self,
        *,
        func: Callable[_P, Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        lifespan: datetime.timedelta,
    ) -> Any:  # noqa: ANN401
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
        if os.environ.get("NO_CACHE"):
            return func(*args, **kwargs)

        key = self.hash_key(func=func, args=args, kwargs=kwargs)
        result_pair = self.get(key=key)

        if result_pair is not None:
            cached_time, result = result_pair
            if not os.environ.get("RE_CACHE") and (
                datetime.datetime.now() < (cached_time + lifespan)  # noqa: DTZ005
            ):
                return self.decode(data=result)
            self.delete(key=key)
        result = func(*args, **kwargs)
        self.put(key=key, data=self.encode(data=result))
        return result

    def del_func_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Delete the cache for a specific function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cache for.

        """
        ...  # no cov
