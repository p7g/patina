import operator
from collections.abc import Hashable
from typing import cast, Any, Callable, TypeVar

T = TypeVar("T")


def dependent_hash(attr_name: str) -> Callable:
    def make_hash(self: T):
        value = getattr(self, attr_name)
        if not isinstance(value, Hashable):
            return None

        def __hash__():
            return hash((type(self), value))

        return __hash__

    return cast(Callable, property(make_hash))


def dependent_ord(attr_name: str):
    def make_ordering_function(name: str) -> Callable[[T, Any], bool]:
        assert hasattr(operator, name)
        op = getattr(operator, name)

        def ordering_function(self: T, other: Any) -> bool:
            if type(other) is not type(self):
                return NotImplemented
            a, b = getattr(self, attr_name), getattr(other, attr_name)
            return op(a, b)

        ordering_function.__name__ = name
        return ordering_function

    def decorate(cls: T) -> T:
        ordering_attrs = ("__lt__", "__le__", "__eq__", "__ne__", "__ge__", "__gt__")
        for attr in ordering_attrs:
            setattr(cls, attr, make_ordering_function(attr))
        return cls

    return decorate
