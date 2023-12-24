from __future__ import annotations

import os
import tempfile
from time import perf_counter
from time import sleep

import pytest
from persistent_cache_decorator import CacheBackend
from persistent_cache_decorator import JsonCacheBackend
from persistent_cache_decorator import persistent_cache
from persistent_cache_decorator import PickleCacheBackend
from persistent_cache_decorator import SqliteCacheBackend


@pytest.mark.parametrize('cache_backend', [(SqliteCacheBackend), (PickleCacheBackend), (JsonCacheBackend)])
def test_persistent_cache(cache_backend: type[CacheBackend]):
    with tempfile.NamedTemporaryFile() as f:
        @persistent_cache(backend=cache_backend(f.name), duration={'seconds': 4})
        def foo(time: float) -> float:
            sleep(time)
            return time

        sleep_time = 2

        start = perf_counter()
        for _ in range(10):
            foo(sleep_time)

        assert perf_counter() - start < sleep_time + 0.1
        assert os.path.exists(foo.__backend__.__save__())
