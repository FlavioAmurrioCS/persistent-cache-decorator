from __future__ import annotations

import atexit
import functools
import pickle
from contextlib import suppress
from typing import Any

from persistent_cache.backend.json import JsonCacheBackend


class PickleCacheBackend(JsonCacheBackend):
    """
    A cache backend that uses pickle to persist data.

    This backend stores cached results in a dictionary and saves them to a file using pickle.
    The cached results are associated with the function name, arguments, and timestamp.

    Args:
    ----
        filename (str): The path to the file where the cached data will be stored.

    Attributes:
    ----------
        _data (dict[str, dict[str, tuple[float, Any]]]): The dictionary that holds the cached data.
        file_path (str): The path to the file where the cached data will be stored.

    """

    _data: dict[str, dict[str, tuple[float, Any]]]
    file_path: str

    @functools.cached_property
    def data(self) -> dict[str, dict[str, tuple[float, Any]]]:
        """
        Property that loads the cached data from the file.

        Returns
        -------
            dict[str, dict[str, tuple[float, Any]]]: The dictionary that holds the cached data.

        """
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
