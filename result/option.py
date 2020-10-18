from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Option(Generic[T], ABC):
    pass


class Some(Option[T]):
    def __init__(self, value: T):
        self.value = value

    def __repr__(self):
        return f"Some({repr(self.value)})"


class None_(Option[T]):
    def __repr__(self):
        return "None_"
