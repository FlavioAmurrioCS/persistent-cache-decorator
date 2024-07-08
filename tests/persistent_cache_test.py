from __future__ import annotations

import asyncio
import os
import tempfile
from time import perf_counter
from time import sleep
from typing import NamedTuple
from unittest.mock import patch

import pytest
from persistent_cache.backend.json import JsonCacheBackend
from persistent_cache.backend.pickle import PickleCacheBackend
from persistent_cache.backend.sqlite import SqliteCacheBackend
from persistent_cache.decorators import persistent_cache
from persistent_cache.decorators import persistent_cached_property


class Person(NamedTuple):
    name: str
    b: int


def _foo(*, time: float) -> Person:
    sleep(time)
    return Person("John", int(time))


async def _foo_async(*, time: float) -> Person:
    await asyncio.sleep(time)
    return Person("John", int(time))


class Temp:
    def foo(self, *, time: float) -> Person:
        return _foo(time=time)


@pytest.mark.parametrize(
    "cache_backend", [(SqliteCacheBackend), (PickleCacheBackend), (JsonCacheBackend)]
)
def test_persistent_cache(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:
        backend = cache_backend(f.name)
        foo = persistent_cache(backend=backend, seconds=4)(_foo)

        sleep_time = 0.2
        loop = 4

        start = perf_counter()
        for _ in range(loop):
            result = foo(time=sleep_time)

        assert perf_counter() - start < sleep_time * loop
        assert os.path.exists(backend.__save__())
        if isinstance(backend, (JsonCacheBackend, PickleCacheBackend)):
            del backend.data
        if not isinstance(backend, JsonCacheBackend):
            result = foo(time=sleep_time)
            assert result == Person("John", int(sleep_time))
        foo.cache_clear()
        assert os.path.exists(backend.__save__())


@pytest.mark.parametrize(
    "cache_backend", [(SqliteCacheBackend), (PickleCacheBackend), (JsonCacheBackend)]
)
def test_persistent_cache_methods(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:
        backend = cache_backend(f.name)
        temp = Temp()
        temp.foo = persistent_cache(backend=backend, seconds=4)(temp.foo)  # type:ignore[method-assign]

        sleep_time = 0.2
        loop = 4

        start = perf_counter()
        for _ in range(loop):
            result = temp.foo(time=sleep_time)

        assert perf_counter() - start < sleep_time * loop
        assert os.path.exists(backend.__save__())
        if isinstance(backend, (JsonCacheBackend, PickleCacheBackend)):
            del backend.data
        if not isinstance(backend, JsonCacheBackend):
            result = temp.foo(time=sleep_time)
            assert result == Person("John", int(sleep_time))
        temp.foo.cache_clear()
        assert os.path.exists(backend.__save__())


@pytest.mark.parametrize(
    "cache_backend",
    [
        (SqliteCacheBackend),
        (PickleCacheBackend),
        (JsonCacheBackend),
    ],
)
def test_persistent_cache_methods2(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:
        backend = cache_backend(f.name)
        with patch.object(
            Temp, "foo", persistent_cached_property(backend=backend, seconds=4)(Temp.foo)
        ):
            temp = Temp()

            sleep_time = 0.2
            loop = 4

            start = perf_counter()
            for _ in range(loop):
                result = temp.foo(time=sleep_time)

            assert perf_counter() - start < sleep_time * loop
            assert os.path.exists(backend.__save__())
            if isinstance(backend, (JsonCacheBackend, PickleCacheBackend)):
                del backend.data
            if not isinstance(backend, JsonCacheBackend):
                result = temp.foo(time=sleep_time)
                assert result == Person("John", int(sleep_time))
            Temp.foo.cache_clear()  # type:ignore[attr-defined]
            assert os.path.exists(backend.__save__())


pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio()
@pytest.mark.parametrize(
    "cache_backend", [(SqliteCacheBackend), (PickleCacheBackend), (JsonCacheBackend)]
)
async def test_persistent_cache_async(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:
        backend = cache_backend(f.name)
        foo = persistent_cache(backend=backend, seconds=4)(_foo_async)

        sleep_time = 0.2
        loop = 4

        start = perf_counter()
        for _ in range(loop):
            result = await foo(time=sleep_time)

        assert perf_counter() - start < sleep_time * loop
        assert os.path.exists(backend.__save__())
        if isinstance(backend, (JsonCacheBackend, PickleCacheBackend)):
            del backend.data
        if not isinstance(backend, JsonCacheBackend):
            result = await foo(time=sleep_time)
            assert result == Person("John", int(sleep_time))
        foo.cache_clear()
        assert os.path.exists(backend.__save__())
