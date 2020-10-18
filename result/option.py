from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Option(Generic[T], ABC):
    pass


class Some(Option[T]):
    def __init__(self, value: T):
        self.value = value


class None_(Option[T]):
    pass
