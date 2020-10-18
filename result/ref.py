from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Ref(Generic[T]):
    """A simulation of a pointer using closures"""

    __slots__ = ("_get", "_set")

    def __init__(self, get: Callable[[], T], set: Callable[[T], None]):
        self._get = get
        self._set = set

    def get(self) -> T:
        """Deference this ref to get the current value at the remote location."""
        return self._get()

    def set(self, value: T):
        """Update the value at the remote location."""
        self._set(value)
