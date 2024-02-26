from __future__ import annotations

import os
import tempfile
from time import perf_counter
from time import sleep

import pytest  # pyright: ignore[reportMissingImports]
from persistent_cache.backend.json import JsonCacheBackend
from persistent_cache.backend.pickle import PickleCacheBackend
from persistent_cache.backend.sqlite import SqliteCacheBackend
from persistent_cache.decorators import persistent_cache
from persistent_cache.decorators import persistent_cached_property


@pytest.mark.parametrize(
    "cache_backend", [(SqliteCacheBackend), (PickleCacheBackend), (JsonCacheBackend)]
)
def test_persistent_cache(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:

        @persistent_cache(backend=cache_backend(f.name), seconds=4)
        def foo(time: float) -> float:
            sleep(time)
            return time

        sleep_time = 0.2

        start = perf_counter()
        for _ in range(10):
            foo(sleep_time)

        assert perf_counter() - start < sleep_time + 0.1
        foo.cache_clear()
        assert os.path.exists(foo.__backend__.__save__())


@pytest.mark.parametrize(
    "cache_backend", [(SqliteCacheBackend), (PickleCacheBackend), (JsonCacheBackend)]
)
def test_persistent_cache_methods(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:

        class Temp:
            def __init__(self) -> None:
                self.foo = persistent_cache(backend=cache_backend(f.name), seconds=4)(
                    self._uncached_foo
                )

            def _uncached_foo(self, time: float) -> float:
                sleep(time)
                return time

        temp = Temp()

        sleep_time = 0.2

        start = perf_counter()
        for _ in range(10):
            temp.foo(sleep_time)

        assert perf_counter() - start < sleep_time + 0.1
        temp.foo.cache_clear()
        assert os.path.exists(temp.foo.__backend__.__save__())


@pytest.mark.parametrize(
    "cache_backend",
    [
        # (SqliteCacheBackend),
        # (PickleCacheBackend),
        (JsonCacheBackend)
    ],
)
def test_persistent_cache_methods2(
    cache_backend: type[SqliteCacheBackend | PickleCacheBackend | JsonCacheBackend],
) -> None:
    with tempfile.NamedTemporaryFile() as f:

        class Temp:
            @persistent_cached_property(backend=cache_backend(f.name), seconds=4)
            def foo(self, *, time: float) -> float:
                sleep(time)
                return time

        temp = Temp()

        sleep_time = 0.2

        start = perf_counter()
        for _ in range(10):
            temp.foo(time=sleep_time)

        assert perf_counter() - start < sleep_time + 0.1
        Temp.foo.cache_clear()
        assert os.path.exists(Temp.foo.__backend__.__save__())
