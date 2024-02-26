# persistent-cache-decorator

[![PyPI - Version](https://img.shields.io/pypi/v/persistent-cache-decorator.svg)](https://pypi.org/project/persistent-cache-decorator)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/persistent-cache-decorator.svg)](https://pypi.org/project/persistent-cache-decorator)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/FlavioAmurrioCS/persistent-cache-decorator/main.svg)](https://results.pre-commit.ci/latest/github/FlavioAmurrioCS/persistent-cache-decorator/main)

-----

**Table of Contents**

- [persistent-cache-decorator](#persistent-cache-decorator)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Cached Property](#cached-property)
  - [Creating a custom cache backend](#creating-a-custom-cache-backend)
  - [License](#license)

## Installation

```console
pip install persistent-cache-decorator
```

## Usage
```python
from __future__ import annotations

import time

from persistent_cache.backend import CacheBackend
from persistent_cache.decorators import json_cache
from persistent_cache.decorators import persistent_cache


@persistent_cache(minutes=4)
def long_func(n: int) -> str:
    """Long Func Documentation."""
    # Long function
    time.sleep(n)
    return f"{n}"


# reveal_type(long_func)
# Runtime type is "_persistent_cache"
# <persistent_cache_decorator._persistent_cache object at 0x10468be50>

# Call function(takes 5 seconds)
long_func(5)
"5"
# Call function again (takes 0 seconds)
long_func(5)
"5"

# Bypass caching(takes 5 seconds)
long_func.no_cache_call(5)
"5"

# Call function again (takes 0 seconds)
long_func(5)
"5"
# Clear cache for this function
long_func.cache_clear()

# Call function(takes 5 seconds)
long_func(5)
```

## Cached Property
```python
from typing import NamedTuple  # noqa: E402
from persistent_cache.decorators import json_cached_property  # noqa: E402


# To cache instance methods, use the json_cache decorator you can do the following:
# Reference: https://www.youtube.com/watch?v=sVjtp6tGo0g
class Pet:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age
        # creating the cache function this way will allow the cache to be cleared using the instance
        # It will also only use the arguments as the key
        self.online_information = json_cache(days=2)(self._online_information)

    def _online_information(self, source: str) -> int:
        # Something that takes a long time
        return len(source)


pet = Pet("Rex", 5)
pet.online_information(source="https://api.github.com/users/rex")
pet.online_information.cache_clear()


# NEW: or you can use the json_cached_property decorator to cache the result of a method
# This makes use of Python's Descriptors: https://www.youtube.com/watch?v=vBys0SwYvCQ
class Person(NamedTuple):
    name: str
    age: int

    # The decorator works with Namedtuples as well as with classes
    @json_cached_property(days=2)
    def online_information(self, source: str) -> int:
        # Something that takes a long time
        return len(source)


person = Person("John", 30)

# The following call will cache the result using the class instance as well as the arguments as the key  # noqa: E501
person.online_information(source="https://api.github.com/users/john")

# To clear the cache, use the method from the class directly
Person.online_information.cache_clear()
```

## Creating a custom cache backend

```python
from typing_extensions import Any  # noqa: E402
from typing import Callable  # noqa: E402
from persistent_cache.decorators import cache_decorator_factory  # noqa: E402
from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    import datetime
    from persistent_cache.decorators import _R


# Define a custom cache backend
class RedisCacheBackend(CacheBackend):
    def get_cache_or_call(  # type: ignore[empty-body]
        self,
        *,
        func: Callable[..., _R],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        lifespan: datetime.timedelta,
    ) -> _R:
        ...

    def del_func_cache(self, *, func: Callable[..., Any]) -> None:
        ...


# Singleton Instance
REDIS_CACHE_BACKEND = RedisCacheBackend()

# Quick way of defining a decorator. You can use this if you want multiple decorators with different cache durations.  # noqa: E501
redis_cache = cache_decorator_factory(backend=REDIS_CACHE_BACKEND)


@redis_cache(days=1)
def foo(time: float) -> float:
    from time import sleep

    sleep(time)
    return time
```

## License

`persistent-cache-decorator` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
