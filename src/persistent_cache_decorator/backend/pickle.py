from __future__ import annotations

import atexit
import datetime
import functools
import pickle
from contextlib import suppress
from typing import Any
from typing import Callable
from typing import Generic
from typing import TypeVar

_R = TypeVar('_R')


class PickleCacheBackend(Generic[_R]):
    _data: dict[str, dict[str, tuple[datetime.datetime, _R]]] = {}
    file_path: str

    def __init__(self, filename: str) -> None:
        self.file_path = filename

    @functools.cached_property
    def data(self) -> dict[str, dict[str, tuple[datetime.datetime, _R]]]:
        with suppress(Exception):
            with open(self.file_path, 'rb') as f:
                self._data = pickle.load(f)
        atexit.register(self.__save__)
        return self._data

    def __save__(self) -> str:
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.data, f)
        return self.file_path

    def get_cached_results(self, *, func: Callable[..., _R], args: tuple[Any, ...], kwargs: dict[str, Any], lifespan: datetime.timedelta) -> _R:
        funcname = func.__qualname__
        args_key = f'args: {args}, kwargs: {kwargs}'
        date, result = self.data.get(funcname, {}).get(args_key, (None, None))
        if date is None or datetime.datetime.now() - date > lifespan:
            result = func(*args, **kwargs)
            self.data.setdefault(funcname, {})[args_key] = (
                datetime.datetime.now(), result,
            )
        return result  # type:ignore

    def del_function_cache(self, *, func: Callable[..., _R]) -> None:
        del self.data[func.__qualname__]
