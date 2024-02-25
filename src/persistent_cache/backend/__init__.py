from __future__ import annotations

import datetime
import os
from typing import Any
from typing import Callable

from typing_extensions import ParamSpec
from typing_extensions import Protocol
from typing_extensions import TypeVar


_P = ParamSpec("_P")
_KEY_T = TypeVar("_KEY_T")
_STORE_T = TypeVar("_STORE_T")


class _CacheBackend(Protocol):
    """Interface for cache backends used by the persistent cache decorator."""

    def get_cached_results(
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

    def del_function_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Delete the cache for a specific function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cache for.

        """
        ...  # no cov


class CacheBackendBase(_CacheBackend, Protocol[_KEY_T, _STORE_T]):
    """Interface for cache backends used by the persistent cache decorator."""

    def get_hash_key(
        self,
        *,
        func: Callable[_P, Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> tuple[str, _KEY_T]:
        return func.__qualname__, f"args: {args}, kwargs: {kwargs}"  # type: ignore

    def get_cached_result(self, *, key: tuple[str, _KEY_T]) -> tuple[float, _STORE_T] | None:
        ...

    def set_cached_result(self, *, key: tuple[str, _KEY_T], data: _STORE_T) -> None:
        ...

    def data_decode(self, *, data: _STORE_T) -> Any:  # noqa: ANN401
        return data

    def data_encode(self, *, data: Any) -> _STORE_T:  # noqa: ANN401
        return data

    def get_cached_results(
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
        key = self.get_hash_key(func=func, args=args, kwargs=kwargs)
        result_pair = self.get_cached_result(key=key)
        if (
            os.environ.get("RE_CACHE")
            or result_pair is None
            or datetime.datetime.now() - datetime.datetime.fromtimestamp(result_pair[0]) > lifespan  # noqa: DTZ005, DTZ006
        ):
            result = func(*args, **kwargs)
            self.set_cached_result(key=key, data=self.data_encode(data=result))
            return result
        return self.data_decode(data=result_pair[1])

    def del_function_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Delete the cache for a specific function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cache for.

        """
        ...  # no cov


# funcname = func.__qualname__
# args_key = f"args: {args}, kwargs: {kwargs}"
# date, result = self.data.get(funcname, {}).get(args_key, (None, None))
# if (
#     os.environ.get("RE_CACHE")
#     or date is None
#     or datetime.datetime.now() - datetime.datetime.fromtimestamp(date) > lifespan
# ):
#     result = func(*args, **kwargs)
#     self.data.setdefault(funcname, {})[args_key] = (
#         datetime.datetime.now().timestamp(),
#         result,
#     )
# return result  # type:ignore
