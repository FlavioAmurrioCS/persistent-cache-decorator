from __future__ import annotations

import atexit
import datetime
import functools
import json
from contextlib import suppress
from typing import Any
from typing import Callable
from typing import Generic
from typing import TypeVar

_R = TypeVar('_R')


class JsonCacheBackend(Generic[_R]):
    _data: dict[str, dict[str, tuple[float, _R]]] = {}
    file_path: str

    def __init__(self, filename: str) -> None:
        self.file_path = filename

    @functools.cached_property
    def data(self) -> dict[str, dict[str, tuple[float, _R]]]:
        with suppress(Exception):
            with open(self.file_path) as f:
                self._data = json.load(f)
        atexit.register(self.__save__)
        return self._data

    def __save__(self) -> str:
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f)
        return self.file_path

    def get_cached_results(self, *, func: Callable[..., _R], args: tuple[Any, ...], kwargs: dict[str, Any], lifespan: datetime.timedelta) -> _R:
        funcname = func.__qualname__
        args_key = f'args: {args}, kwargs: {kwargs}'
        date, result = self.data.get(funcname, {}).get(args_key, (None, None))
        if date is None or datetime.datetime.now() - datetime.datetime.fromtimestamp(date) > lifespan:
            result = func(*args, **kwargs)
            self.data.setdefault(funcname, {})[args_key] = (
                datetime.datetime.now().timestamp(), result,
            )
        return result  # type:ignore

    def del_function_cache(self, *, func: Callable[..., _R]) -> None:
        del self.data[func.__qualname__]
