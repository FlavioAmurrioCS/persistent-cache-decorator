from __future__ import annotations

import datetime
import functools
import pickle
import sqlite3
from typing import Any
from typing import Callable
from typing import Tuple

from persistent_cache.backend import AbstractCacheBackend
from persistent_cache.backend import CacheBackendDecodeError
from persistent_cache.backend import CacheBackendEncodeError
from persistent_cache.backend import get_function_identifier


class SqliteCacheBackend(AbstractCacheBackend[Tuple[bytes, bytes], bytes]):
    """
    A cache backend implementation using SQLite as the storage.

    Args:
    ----
        filename (str): The path to the SQLite database file.

    Attributes:
    ----------
        file_path (str): The path to the SQLite database file.

    Methods:
    -------
        __save__(): Returns the file path of the SQLite database.
        connection(): Returns a SQLite connection object.
        cursor(): Returns a SQLite cursor object.
        get_cached_results(): Retrieves cached results from the cache.
        del_function_cache(): Deletes cached results for a specific function.

    """

    file_path: str

    def __init__(self, filename: str) -> None:
        self.file_path = filename

    def __save__(self) -> str:
        """
        Returns the file path of the SQLite database.

        Returns
        -------
            str: The file path of the SQLite database.

        """
        return self.file_path

    @functools.cached_property
    def connection(self) -> sqlite3.Connection:
        """
        Returns a SQLite connection object.

        Returns
        -------
            sqlite3.Connection: A SQLite connection object.

        """
        return sqlite3.connect(self.file_path)

    @functools.cached_property
    def cursor(self) -> sqlite3.Cursor:
        """
        Returns a SQLite cursor object.

        Returns
        -------
            sqlite3.Cursor: A SQLite cursor object.

        """
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                function TEXT,
                args BLOB,
                kwargs BLOB,
                result BLOB,
                timestamp TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
            )
        """
        )
        connection.commit()
        return cursor

    def hash_key(
        self, *, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> tuple[str, tuple[bytes, bytes]]:
        pickled_args = pickle.dumps(args)
        pickled_kwargs = pickle.dumps(kwargs)
        return (get_function_identifier(func), (pickled_args, pickled_kwargs))

    def encode(self, *, data: Any) -> Any:  # noqa: ANN401
        try:
            return pickle.dumps(data)
        except (pickle.PickleError, TypeError) as e:
            raise CacheBackendEncodeError(e) from None

    def decode(self, *, data: Any) -> Any:  # noqa: ANN401
        try:
            return pickle.loads(data)  # noqa: S301
        except (pickle.PickleError, TypeError) as e:
            raise CacheBackendDecodeError(e) from None

    def get(
        self, *, key: tuple[str, tuple[bytes, bytes]]
    ) -> tuple[datetime.datetime, bytes] | None:
        func_key, (args_key, kwargs_key) = key
        self.cursor.execute(
            """
            SELECT result, timestamp FROM cache
            WHERE function = ? AND args = ? AND kwargs = ?
        """,
            (func_key, args_key, kwargs_key),
        )
        cached_result = self.cursor.fetchone()
        if not cached_result:
            return None

        pickled_result, timestamp = cached_result
        cached_time = datetime.datetime.strptime(  # noqa: DTZ007
            timestamp,
            "%Y-%m-%d %H:%M:%S",
        )
        return cached_time, pickled_result

    def delete(self, *, key: tuple[str, tuple[bytes, bytes]]) -> None:
        funcname, (pickled_args, pickled_kwargs) = key
        self.cursor.execute(
            """
            DELETE FROM cache
            WHERE function = ? AND args = ? AND kwargs = ?
        """,
            (funcname, pickled_args, pickled_kwargs),
        )
        self.connection.commit()

    def put(self, *, key: tuple[str, tuple[bytes, bytes]], data: bytes) -> None:
        funcname, (pickled_args, pickled_kwargs) = key
        self.cursor.execute(
            """
            INSERT INTO cache (function, args, kwargs, result)
            VALUES (?, ?, ?, ?)
        """,
            (funcname, pickled_args, pickled_kwargs, data),
        )
        self.connection.commit()

    def del_func_cache(self, *, func: Callable[..., Any]) -> None:
        """
        Deletes cached results for a specific function.

        Args:
        ----
            func (Callable[..., Any]): The function to delete cached results for.

        """
        self.cursor.execute(
            """
            DELETE FROM cache
            WHERE function = ?
            """,
            (get_function_identifier(func),),
        )
        self.connection.commit()
