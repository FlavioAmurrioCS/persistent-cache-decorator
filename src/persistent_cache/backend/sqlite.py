from __future__ import annotations

import datetime
import functools
import pickle
import sqlite3
from typing import Any
from typing import Callable

from typing_extensions import TypeVar


_R = TypeVar("_R")


class SqliteCacheBackend:
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

    def get_cached_results(
        self,
        *,
        func: Callable[..., _R],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        lifespan: datetime.timedelta,
    ) -> _R:
        """
        Retrieves cached results from the cache.

        Args:
        ----
            func (Callable[..., _R]): The function to retrieve cached results for.
            args (tuple[Any, ...]): The arguments passed to the function.
            kwargs (dict[str, Any]): The keyword arguments passed to the function.
            lifespan (datetime.timedelta): The lifespan of the cached results.

        Returns:
        -------
            _R: The cached results, if available. Otherwise, the function is called and the results are cached.

        """  # noqa: E501
        # Serialize the arguments and keyword arguments
        pickled_args = pickle.dumps(args)
        pickled_kwargs = pickle.dumps(kwargs)

        # region: Get cached entry
        self.cursor.execute(
            """
            SELECT result, timestamp FROM cache
            WHERE function = ? AND args = ? AND kwargs = ?
        """,
            (func.__qualname__, pickled_args, pickled_kwargs),
        )
        cached_result = self.cursor.fetchone()
        # endregion: Get cached entry

        if cached_result:
            pickled_result, timestamp = cached_result
            cached_time = datetime.datetime.strptime(  # noqa: DTZ007
                timestamp,
                "%Y-%m-%d %H:%M:%S",
            )

            if datetime.datetime.now() < cached_time + lifespan:  # noqa: DTZ005
                return pickle.loads(pickled_result)  # noqa: S301

            # region: Delete expired cache entry
            self.cursor.execute(
                """
                DELETE FROM cache
                WHERE function = ? AND args = ? AND kwargs = ?
            """,
                (func.__qualname__, pickled_args, pickled_kwargs),
            )
            self.connection.commit()
            # endregion: Delete expired cache entry

        result = func(*args, **kwargs)

        # region: Save result to cache
        pickled_result = pickle.dumps(result)
        self.cursor.execute(
            """
            INSERT INTO cache (function, args, kwargs, result)
            VALUES (?, ?, ?, ?)
        """,
            (func.__qualname__, pickled_args, pickled_kwargs, pickled_result),
        )
        self.connection.commit()
        # endregion: Save result to cache

        return result

    def del_function_cache(self, *, func: Callable[..., Any]) -> None:
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
            (func.__qualname__,),
        )
        self.connection.commit()
