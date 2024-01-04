# persistent-cache-decorator

[![PyPI - Version](https://img.shields.io/pypi/v/persistent-cache-decorator.svg)](https://pypi.org/project/persistent-cache-decorator)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/persistent-cache-decorator.svg)](https://pypi.org/project/persistent-cache-decorator)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/FlavioAmurrioCS/persistent-cache-decorator/main.svg)](https://results.pre-commit.ci/latest/github/FlavioAmurrioCS/persistent-cache-decorator/main)

-----

**Table of Contents**

- [persistent-cache-decorator](#persistent-cache-decorator)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Creating a custom cache backend](#creating-a-custom-cache-backend)
  - [License](#license)

## Installation

```console
pip install persistent-cache-decorator
```

## Usage
```python
>>> from typing import reveal_type
>>> from persistent_cache.decorators import persistent_cache
>>> # from persistent_cache.decorators import json_cache # Can also use one of this specific cache methods
>>> # from persistent_cache.decorators import pickle_cache # Can also use one of this specific cache methods
>>> # from persistent_cache.decorators import sqlite_cache # Can also use one of this specific cache methods
>>>
>>> import time
>>>
>>> @persistent_cache(minutes=4)
... def long_func(n: int) -> str:
...     """Long Func Documentation"""
...     # Long function
...     time.sleep(n)
...     return f"{n}"
...
>>> reveal_type(long_func)
Runtime type is '_persistent_cache'
<persistent_cache_decorator._persistent_cache object at 0x10468be50>
>>>
>>> # Call function(takes 5 seconds)
>>> long_func(5)
'5'
>>> # Call function again (takes 0 seconds)
>>> long_func(5)
'5'
>>>
>>> # Bypass caching(takes 5 seconds)
>>> long_func.no_cache_call(5)
'5'
>>>
>>> # Call function again (takes 0 seconds)
>>> long_func(5)
'5'
>>> # Clear cache for this function
>>> long_func.cache_clear()
>>>
>>> # Call function(takes 5 seconds)
>>> long_func(5)
```

## Creating a custom cache backend

```python
# Define a custom cache backend
class RedisCacheBackend:
    def get_cached_results(self, *, func: Callable[..., _R], args: tuple[Any, ...], kwargs: dict[str, Any], lifespan: datetime.timedelta) -> _R: ...
    def del_function_cache(self, *, func: Callable[..., Any]) -> None: ...

# Singleton Instance
REDIS_CACHE_BACKEND = RedisCacheBackend()

# Quick way of defining a decorator. You can use this if you want multiple decorators with different cache durations.
# It does have some typing hinting issues though :/
quick_redis_cache = cache_decorator_factory(backend=REDIS_CACHE_BACKEND)

@quick_redis_cache(days=1)
def foo(time: float) -> float:
    from time import sleep
    sleep(time)
    return time

# This is the recommended way of defining a decorator. It has better typing hinting.
def redis_cache(
    **duration: Unpack[_cache_duration]
) -> Callable[[Callable[_P, _R]], _persistent_cache[_P, _R, RedisCacheBackend]]:
    duration = duration or {'days': 1}  # You can set your own default cache duration.
    mcache_duration = datetime.timedelta(**duration)

    def inner(func: Callable[_P, _R]) -> _persistent_cache[_P, _R, RedisCacheBackend]:
        return _persistent_cache(
            func=func,
            duration=mcache_duration,
            backend=REDIS_CACHE_BACKEND,
        )
    return inner

@redis_cache(days=1, seconds=1)
def foo2(time: float) -> float:
    from time import sleep
    sleep(time)
    return time

```

## License

`persistent-cache-decorator` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
