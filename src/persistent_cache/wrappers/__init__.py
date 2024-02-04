from __future__ import annotations

import functools
from functools import _CacheInfo
from functools import _lru_cache_wrapper
from functools import lru_cache as _lru_cache
from typing import Callable
from typing import Generic
from typing import TypeVar

from typing_extensions import ParamSpec

_R = TypeVar("_R")
_P = ParamSpec("_P")


class _LRUCache(Generic[_P, _R]):
    __wrapped__: Callable[_P, _R]
    __wrapped_lru_func__: _lru_cache_wrapper[_R]

    def __init__(
        self, *, func: Callable[_P, _R], maxsize: int | None = 128, typed: bool = False
    ) -> None:
        self.__wrapped__ = func
        self.__wrapped_lru_func__: _lru_cache_wrapper[_R] = _lru_cache(
            maxsize=maxsize, typed=typed
        )(self.__wrapped__)
        functools.update_wrapper(self, func)

    def cache_info(self) -> _CacheInfo:
        return self.__wrapped_lru_func__.cache_info()

    def cache_clear(self) -> None:
        return self.__wrapped_lru_func__.cache_clear()

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        return self.__wrapped_lru_func__(*args, **kwargs)  # type: ignore

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


def lru_cache(
    *, maxsize: int | None = 128, typed: bool = False
) -> Callable[[Callable[_P, _R]], _LRUCache[_P, _R]]:
    return lambda func: _LRUCache(func=func, maxsize=maxsize, typed=typed)
