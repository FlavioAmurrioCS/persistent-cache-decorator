from __future__ import annotations

import atexit
import functools
import json
from contextlib import suppress
from datetime import datetime
from typing import Any
from typing import Callable

from persistent_cache.backend import CacheBackendBase


class JsonCacheBackend(CacheBackendBase[str, Any]):
    """
    A cache backend that stores cached results in a JSON file.

    This backend uses a dictionary to store the cached results, where the keys are function names
    and the values are dictionaries that map argument keys to tuples of timestamp and result.

    Args:
    ----
        filename (str): The path to the JSON file used for storing the cached results.

    Attributes:
    ----------
        _data (dict[str, dict[str, tuple[float, Any]]]): The dictionary that stores the cached results.
        file_path (str): The path to the JSON file used for storing the cached results.

    """  # noqa: E501

    _data: dict[str, dict[str, tuple[float, Any]]]
    file_path: str

    def __init__(self, filename: str) -> None:
        self._data = {}
        self.file_path = filename

    @functools.cached_property
    def data(self) -> dict[str, dict[str, tuple[float, Any]]]:
        """
        Property that lazily loads the cached results from the JSON file.

        Returns
        -------
            dict[str, dict[str, tuple[float, Any]]]: The dictionary that stores the cached results.

        """
        with suppress(Exception), open(self.file_path) as f:
            self._data = json.load(f)
        atexit.register(self.__save__)
        return self._data

    def __save__(self) -> str:
        """
        Saves the cached results to the JSON file.

        Returns
        -------
            str: The path to the JSON file.

        """
        with open(self.file_path, "w") as f:
            json.dump(self.data, f)
        return self.file_path

    def get_cached_result(self, *, key: tuple[str, str]) -> tuple[float, Any] | None:
        funcname, args_key = key
        result_pair = self.data.get(funcname, {}).get(args_key, None)
        if result_pair is None:
            return None
        date, data = result_pair
        return date, data

    def set_cached_result(self, *, key: tuple[str, str], data: Any) -> None:  # noqa: ANN401
        funcname, args_key = key
        self.data.setdefault(funcname, {})[args_key] = (
            datetime.now().timestamp(),  # noqa: DTZ005
            data,
        )

    def del_function_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Deletes the cached results for a given function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cached results for.

        """
        del self.data[func.__qualname__]
