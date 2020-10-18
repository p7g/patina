from abc import ABC, abstractmethod
from typing import Any, cast, Callable, Generic, Iterator, Type, TypeVar

from .option import Option, Some, None_
from ._utils import dependent_hash, dependent_ord

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Result(Generic[T, E], ABC):
    @abstractmethod
    def is_ok(self) -> bool:
        ...

    @abstractmethod
    def is_err(self) -> bool:
        ...

    @abstractmethod
    def ok(self) -> Option[T]:
        ...

    @abstractmethod
    def err(self) -> Option[E]:
        ...

    @abstractmethod
    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        ...

    @abstractmethod
    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        ...

    @abstractmethod
    def map_or_else(self, default: Callable[[E], U], f: Callable[[T], U]) -> U:
        ...

    @abstractmethod
    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        ...

    @abstractmethod
    def iter(self) -> Iterator[T]:
        ...

    def __iter__(self) -> Iterator[T]:
        return self.iter()

    @abstractmethod
    def and_(self, res: "Result[U, E]") -> "Result[U, E]":
        ...

    @abstractmethod
    def and_then(self, op: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        ...

    @abstractmethod
    def or_(self, res: "Result[T, F]") -> "Result[T, F]":
        ...

    @abstractmethod
    def or_else(self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        ...

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        ...

    @abstractmethod
    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        ...

    @abstractmethod
    def expect(self, msg: str) -> T:
        ...

    @abstractmethod
    def unwrap(self) -> T:
        ...

    @abstractmethod
    def expect_err(self, msg: str) -> E:
        ...

    @abstractmethod
    def unwrap_err(self) -> E:
        ...


@dependent_ord('value')
class Ok(Result[T, E]):
    def __init__(self, value: T):
        self.value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def ok(self) -> Option[T]:
        return Some(self.value)

    def err(self) -> Option[E]:
        return None_()

    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        return cast(Type[Ok[U, E]], type(self))(op(self.value))

    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        return f(self.value)

    def map_or_else(self, default: Callable[[E], U], f: Callable[[T], U]) -> U:
        return f(self.value)

    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        return cast(Ok[T, F], self)

    def iter(self) -> Iterator[T]:
        yield self.value

    def and_(self, res: "Result[U, E]") -> "Result[U, E]":
        return res

    def and_then(self, op: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return op(self.value)

    def or_(self, res: "Result[T, F]") -> "Result[T, F]":
        return cast(Ok[T, F], self)

    def or_else(self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        return cast(Ok[T, F], self)

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        return self.value

    def expect(self, msg: str) -> T:
        return self.value

    def unwrap(self) -> T:
        return self.value

    def expect_err(self, msg: str) -> E:
        raise AssertionError(msg)

    def unwrap_err(self) -> E:
        raise AssertionError(self.value)

    def __repr__(self):
        return f"Ok({repr(self.value)})"

    def __eq__(self, other: Any):
        if type(self) is not type(other):
            return NotImplemented
        return self.value == other.value

    __hash__ = dependent_hash("value")


@dependent_ord('error')
class Err(Result[T, E]):
    def __init__(self, error: E):
        self.error = error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def ok(self) -> Option[T]:
        return None_()

    def err(self) -> Option[E]:
        return Some(self.error)

    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        return cast(Err[U, E], self)

    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        return default

    def map_or_else(self, default: Callable[[E], U], f: Callable[[T], U]) -> U:
        return default(self.error)

    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        return cast(Type[Err[T, F]], type(self))(op(self.error))

    def iter(self) -> Iterator[T]:
        return
        yield

    def and_(self, res: "Result[U, E]") -> "Result[U, E]":
        return cast(Err[U, E], self)

    def and_then(self, op: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return cast(Err[U, E], self)

    def or_(self, res: "Result[T, F]") -> "Result[T, F]":
        return res

    def or_else(self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        return op(self.error)

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        return op(self.error)

    def expect(self, msg: str) -> T:
        raise AssertionError(msg)

    def unwrap(self) -> T:
        raise AssertionError(self.error)

    def expect_err(self, msg: str) -> E:
        return self.error

    def unwrap_err(self) -> E:
        return self.error

    def __repr__(self):
        return f"Err({repr(self.error)})"

    def __eq__(self, other: Any):
        if type(self) is not type(other):
            return NotImplemented
        return self.error == other.error

    __hash__ = dependent_hash("error")
