from __future__ import annotations

import atexit
import datetime
import functools
import pickle
from contextlib import suppress
from typing import Any
from typing import Callable
from typing import TypeVar

_R = TypeVar("_R")


class PickleCacheBackend:
    """
    A cache backend that uses pickle to persist data.

    This backend stores cached results in a dictionary and saves them to a file using pickle.
    The cached results are associated with the function name, arguments, and timestamp.

    Args:
    ----
        filename (str): The path to the file where the cached data will be stored.

    Attributes:
    ----------
        _data (dict[str, dict[str, tuple[datetime.datetime, Any]]]): The dictionary that holds the cached data.
        file_path (str): The path to the file where the cached data will be stored.

    """  # noqa: E501

    _data: dict[str, dict[str, tuple[datetime.datetime, Any]]]
    file_path: str

    def __init__(self, filename: str) -> None:
        self._data = {}
        self.file_path = filename

    @functools.cached_property
    def data(self) -> dict[str, dict[str, tuple[datetime.datetime, Any]]]:
        """
        Property that loads the cached data from the file.

        Returns
        -------
            dict[str, dict[str, tuple[datetime.datetime, Any]]]: The dictionary that holds the cached data.

        """  # noqa: E501
        with suppress(Exception), open(self.file_path, "rb") as f:
            self._data = pickle.load(f)  # noqa: S301
        atexit.register(self.__save__)
        return self._data

    def __save__(self) -> str:
        """
        Saves the cached data to the file.

        Returns
        -------
            str: The path to the file where the cached data was saved.

        """
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)
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
        Retrieves the cached results for a given function, arguments, and lifespan.

        If the cached results are not found or have expired, the function is called and the results are cached.

        Args:
        ----
            func (Callable[..., _R]): The function to retrieve the cached results for.
            args (tuple[Any, ...]): The arguments passed to the function.
            kwargs (dict[str, Any]): The keyword arguments passed to the function.
            lifespan (datetime.timedelta): The maximum lifespan of the cached results.

        Returns:
        -------
            _R: The cached results or the results of calling the function.

        """  # noqa: E501
        funcname = func.__qualname__
        args_key = f"args: {args}, kwargs: {kwargs}"
        date, result = self.data.get(funcname, {}).get(args_key, (None, None))
        if date is None or datetime.datetime.now() - date > lifespan:  # noqa: DTZ005
            result = func(*args, **kwargs)
            self.data.setdefault(funcname, {})[args_key] = (
                datetime.datetime.now(),  # noqa: DTZ005
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
