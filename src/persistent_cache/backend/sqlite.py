from __future__ import annotations

import datetime
import functools
import pickle
import sqlite3
from typing import Any
from typing import Callable
from typing import Generic

from typing_extensions import TypeVar


_R = TypeVar('_R')


class SqliteCacheBackend(Generic[_R]):
    file_path: str

    def __init__(self, filename: str) -> None:
        self.file_path = filename

    @functools.cached_property
    def connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.file_path)

    @functools.cached_property
    def cursor(self) -> sqlite3.Cursor:
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                function TEXT,
                args BLOB,
                kwargs BLOB,
                result BLOB,
                timestamp TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
            )
        ''')
        connection.commit()
        return cursor

    def get_cached_results(self, *, func: Callable[..., _R], args: tuple[Any, ...], kwargs: dict[str, Any], lifespan: datetime.timedelta) -> _R:
        # Serialize the arguments and keyword arguments
        pickled_args = pickle.dumps(args)
        pickled_kwargs = pickle.dumps(kwargs)

        # region: Get cached entry
        self.cursor.execute(
            '''
            SELECT result, timestamp FROM cache
            WHERE function = ? AND args = ? AND kwargs = ?
        ''', (func.__qualname__, pickled_args, pickled_kwargs),
        )
        cached_result = self.cursor.fetchone()
        # endregion: Get cached entry

        if cached_result:
            pickled_result, timestamp = cached_result
            cached_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

            if datetime.datetime.now() < cached_time + lifespan:
                return pickle.loads(pickled_result)
            else:
                # region: Delete expired cache entry
                self.cursor.execute(
                    '''
                    DELETE FROM cache
                    WHERE function = ? AND args = ? AND kwargs = ?
                ''', (func.__qualname__, pickled_args, pickled_kwargs),
                )
                self.connection.commit()
                # endregion: Delete expired cache entry

        result = func(*args, **kwargs)

        # region: Save result to cache
        pickled_result = pickle.dumps(result)
        self.cursor.execute(
            '''
            INSERT INTO cache (function, args, kwargs, result)
            VALUES (?, ?, ?, ?)
        ''', (func.__qualname__, pickled_args, pickled_kwargs, pickled_result),
        )
        self.connection.commit()
        # endregion: Save result to cache

        return result

    def del_function_cache(self, *, func: Callable[..., _R]) -> None:
        self.cursor.execute(
            '''
            DELETE FROM cache
            WHERE function = ?
            ''', (func.__qualname__),
        )
        self.connection.commit()
