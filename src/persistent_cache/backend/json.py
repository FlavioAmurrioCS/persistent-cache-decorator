from __future__ import annotations

import atexit
import datetime
import functools
import json
from contextlib import suppress
from typing import Any
from typing import Callable
from typing import TypeVar

_R = TypeVar("_R")


class JsonCacheBackend:
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

    def get_cached_results(
        self,
        *,
        func: Callable[..., _R],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        lifespan: datetime.timedelta,
    ) -> _R:
        """
        Retrieves the cached result for a given function and arguments, or computes and caches the result if it's not available or expired.

        Args:
        ----
            func (Callable[..., _R]): The function to retrieve or compute the result for.
            args (tuple[Any, ...]): The positional arguments for the function.
            kwargs (dict[str, Any]): The keyword arguments for the function.
            lifespan (datetime.timedelta): The maximum lifespan of the cached result.

        Returns:
        -------
            _R: The cached result or the computed result.

        """  # noqa: E501
        funcname = func.__qualname__
        args_key = f"args: {args}, kwargs: {kwargs}"
        date, result = self.data.get(funcname, {}).get(args_key, (None, None))
        if (
            date is None
            or datetime.datetime.now() - datetime.datetime.fromtimestamp(date) > lifespan  # noqa: DTZ005, DTZ006
        ):
            result = func(*args, **kwargs)
            self.data.setdefault(funcname, {})[args_key] = (
                datetime.datetime.now().timestamp(),  # noqa: DTZ005
                result,
            )
        return result  # type:ignore

    def del_function_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Deletes the cached results for a given function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete the cached results for.

        """
        del self.data[func.__qualname__]
