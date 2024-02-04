from __future__ import annotations

import functools
import json
from typing import Callable
from typing import Generic
from typing import overload
from typing import TypeVar

from typing_extensions import Concatenate
from typing_extensions import ParamSpec

Instance = TypeVar("Instance")
Value = TypeVar("Value")
Attribute = TypeVar("Attribute")
P = ParamSpec("P")


class Descriptor(Generic[Instance, Attribute, Value, P]):
    inst: Instance
    method: Callable[Concatenate[Instance, P], Value]

    def __init__(self, method: Callable[Concatenate[Instance, P], Value]) -> None:
        """Called on initialisation of descriptor."""
        self.method = method
        print(json.dumps(locals(), default=str))
        functools.update_wrapper(self, method)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Value:
        """Called when the descriptor is called."""
        print(json.dumps(locals(), default=str))
        return self.method(self.inst, *args, **kwargs)

    @overload
    def __get__(self, instance: None, owner: type[Instance]) -> Descriptor:
        # """Called when an attribute is accessed via class not an instance."""
        ...

    @overload
    def __get__(self, instance: Instance, owner: type[Instance]) -> Callable[P, Value]:
        # """Called when an attribute is accessed on an instance variable."""
        ...

    def __get__(
        self, instance: Instance | None, owner: type[Instance]
    ) -> Callable[P, Value] | Descriptor:
        if instance is None:
            return self
        self.inst = instance
        # return self.method.__get__(instance, owner)
        return self.method.__get__(instance, owner)  # type: ignore
        # return types.MethodType(json_cache()(self.method).__call__, instance, owner)  # type: ignore
        # return types.MethodType(self.method, instance, owner)  # type: ignore
        # return self.method(instance)
        # """Full implementation is declared here."""
        # print(json.dumps(locals(), default=str))
        # ...
        # return None

    # def __set__(self, instance: Instance, value: Value) -> None:
    #     """Called when setting a value."""
    #     print(json.dumps(locals(), default=str))


class Foo:
    @Descriptor
    def bar(self, *, value: int) -> int:
        return value


a = Foo()


a.bar(value=5)


print(a.bar(5))
