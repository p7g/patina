"""Error handling with the Result type.

Result[T, E] is the type used for returning and propagating errors. It is an
enum with the variants, Ok(T), representing success and containing a value, and
Err(E), representing error and containing an error value.

A simple function returning Result might be defined and used like so:

>>> from enum import auto, Enum
>>>
>>> class Version(Enum):
...     version_1 = auto()
...     version_2 = auto()
...
>>> def parse_version(header: bytes) -> Result[Version, str]:
...     if len(header) == 0:
...         return Err("invalid header length")
...     elif header[0] == 1:
...         return Ok(Version.version_1)
...     elif header[0] == 2:
...         return Ok(Version.version_2)
...     else:
...         return Err("invalid version")
...
>>> version = parse_version(bytes([1, 2, 3, 4]))
>>> if isinstance(version, Ok):
...     print(f"working with version: {version.value}")
... else:
...     print(f"error parsing header: {version.error}")
...
working with version: Version.version_1

Pattern matching on `Result`s is clear and straightforward for simple cases (in
Rust), but `Result` comes with some convenience methods that make working with
it more succinct.

>>> good_result: Result[int, int] = Ok(10)
>>> bad_result: Result[int, int] = Err(10)
>>>
>>> # The `is_ok` and `is_err` methods do what they say.
>>> good_result.is_ok() and not good_result.is_err()
True
>>> bad_result.is_err() and not bad_result.is_ok()
True
>>>
>>> # `map` consumes the `Result` (in Rust) and produces another.
>>> good_result: Result[int, int] = good_result.map(lambda i: i + 1)
>>> bad_result: Result[int, int] = bad_result.map(lambda i: i - 1)
>>>
>>> # Use `and_then` to continue their computation.
>>> good_result: Result[bool, int] = good_result.and_then(lambda i: Ok(i == 11))
>>>
>>> # Use `or_else` to handle the error.
>>> bad_result: Result[int, int] = bad_result.or_else(lambda i: Ok(i + 20))
>>>
>>> # Consume the result and return the contents with `unwrap`.
>>> final_awesome_result = good_result.unwrap()
>>> final_awesome_result
True
"""

from abc import ABC, abstractmethod
from typing import Any, cast, Callable, Generic, Iterator, Type, TypeVar

from .option import Option, Some, None_
from ._utils import dependent_hash, dependent_ord

__all__ = ("Result", "Ok", "Err")

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Result(Generic[T, E], ABC):
    """Result is a type that represents either success (Ok) or failure (Err)."""

    @abstractmethod
    def is_ok(self) -> bool:
        """Returns `True` if the result is Ok.

        Basic usage:
        >>> x: Result[int, str] = Ok(-3)
        >>> x.is_ok()
        True

        >>> x: Result[int, str] = Err("Some error message")
        >>> x.is_ok()
        False
        """

    @abstractmethod
    def is_err(self) -> bool:
        """Returns `True` if the result is Err.

        Basic usage:
        >>> x: Result[int, str] = Ok(-3)
        >>> x.is_err()
        False

        >>> x: Result[int, str] = Err("Some error message")
        >>> x.is_err()
        True
        """

    @abstractmethod
    def ok(self) -> Option[T]:
        """Converts from `Result[T, E]` to `Option[T]`.
        Converts `self` into Option[T], discarding the error, if any.

        Basic usage:
        >>> x: Result[int, str] = Ok(2)
        >>> x.ok()
        Some(2)

        >>> x: Result[int, str] = Err("Nothing here")
        >>> x.ok()
        None_
        """

    @abstractmethod
    def err(self) -> Option[E]:
        """Converts from `Result[T, E]` to `Option[E]`.
        Converts `self` into Option[E], discarding the success value, if any.

        Basic usage:
        >>> x: Result[int, str] = Ok(2)
        >>> x.err()
        None_

        >>> x: Result[int, str] = Err("Nothing here")
        >>> x.err()
        Some('Nothing here')
        """

    @abstractmethod
    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        """Maps a `Result[T, E]` to `Result[U, E]` by applying a function to a
        contained Ok value, leaving an Err value untouched.

        This function can be used to compose the results of two functions.

        Print the numbers on each line of a string multiplied by two.
        >>> def try_parse(s: str) -> Result[int, ValueError]:
        ...     try:
        ...         return Ok(int(s))
        ...     except ValueError as e:
        ...         return Err(e)
        ...
        >>> line = "1\\n2\\n3\\n4\\n5\\n"
        >>> for num in line.splitlines():
        ...     result = try_parse(num).map(lambda i: i * 2)
        ...     if isinstance(result, Ok):
        ...         print(result.value)
        2
        4
        6
        8
        10
        """

    @abstractmethod
    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        """Applies a function to the contained value (if Ok), or returns the
        provided default (if Err).

        Arguments passed to `map_or` are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use `map_or_else`,
        which is lazily evaluated.

        >>> x: Result[str, str] = Ok("foo")
        >>> x.map_or(42, lambda v: len(v))
        3

        >>> x: Result[str, str] = Err("bar")
        >>> x.map_or(42, lambda v: len(v))
        42
        """

    @abstractmethod
    def map_or_else(self, default: Callable[[E], U], f: Callable[[T], U]) -> U:
        """Maps a `Result[T, E]` to `U` by applying a function to a contained Ok
        value, or a fallback function to a contained Err value.

        This function can be used to unpack a successful result while handling
        an error.

        Basic usage:
        >>> k = 21

        >>> x: Result[str, str] = Ok("foo")
        >>> x.map_or_else(lambda e: k * 2, lambda v: len(v))
        3

        >>> x: Result[str, str] = Err("foo")
        >>> x.map_or_else(lambda e: k * 2, lambda v: len(v))
        42
        """

    @abstractmethod
    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        """Maps a `Result[T, E]` to `Result[T, F]` by applying a function to a
        contained Err value, leaving an Ok value untouched.

        This function can be used to pass through a successful result while
        handling an error.

        Basic usage:
        >>> def stringify(x: int) -> str:
        ...     return f"error code: {x}"
        ...
        >>> x: Result[int, int] = Ok(2)
        >>> x.map_err(stringify)
        Ok(2)

        >>> x: Result[int, int] = Err(13)
        >>> x.map_err(stringify)
        Err('error code: 13')
        """

    @abstractmethod
    def iter(self) -> Iterator[T]:
        """Returns an iterator over the possibly contained value.

        The iterator yields one value if the reusult is Ok, otherwise none.

        Basic usage:
        >>> x: Result[int, str] = Ok(7)
        >>> next(x.iter())
        7

        >>> x: Result[int, str] = Err("nothing!")
        >>> next(x.iter())
        Traceback (most recent call last):
            ...
        StopIteration
        """

    def __iter__(self) -> Iterator[T]:
        """Returns an iterator over the possibly contained value.

        The iterator yields one value if the reusult is Ok, otherwise none.

        Basic usage:
        >>> x: Result[int, str] = Ok(7)
        >>> next(iter(x))
        7

        >>> x: Result[int, str] = Err("nothing!")
        >>> next(iter(x))
        Traceback (most recent call last):
            ...
        StopIteration
        """
        return self.iter()

    @abstractmethod
    def and_(self, res: "Result[U, E]") -> "Result[U, E]":
        """Returns `res` if the result is Ok, otherwise returns the Err value
        of `self`.

        Basic usage:
        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[str, str] = Err("late error")
        >>> x.and_(y)
        Err('late error')

        >>> x: Result[int, str] = Err("early error")
        >>> y: Result[str, str] = Ok("foo")
        >>> x.and_(y)
        Err('early error')

        >>> x: Result[int, str] = Err("not a 2")
        >>> y: Result[str, str] = Err("late error")
        >>> x.and_(y)
        Err('not a 2')

        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[str, str] = Ok("different result type")
        >>> x.and_(y)
        Ok('different result type')
        """

    @abstractmethod
    def and_then(self, op: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Calls `op` if the result is Ok, otherwise returns the Err value of
        `self`.

        This function can be used for control flow based on `Result` values.

        Basic usage:
        >>> def sq(x: int) -> Result[int, int]: return Ok(x * x)
        ...
        >>> def err(x: int) -> Result[int, int]: return Err(x)
        ...
        >>> Ok(2).and_then(sq).and_then(sq)
        Ok(16)
        >>> Ok(2).and_then(sq).and_then(err)
        Err(4)
        >>> Ok(2).and_then(err).and_then(sq)
        Err(2)
        >>> Err(3).and_then(sq).and_then(sq)
        Err(3)
        """

    @abstractmethod
    def or_(self, res: "Result[T, F]") -> "Result[T, F]":
        """Returns `res` if the result is Err, otherwise returns the Ok result
        of self.

        Arguments passed to or are eagerly evaluated; if you are passing the
        result of a function call, it is recommended to use `or_else`, which is
        lazily evaluated.

        Basic usage:
        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[int, str] = Err("late error")
        >>> x.or_(y)
        Ok(2)

        >>> x: Result[int, str] = Err("early error")
        >>> y: Result[int, str] = Ok(2)
        >>> x.or_(y)
        Ok(2)

        >>> x: Result[int, str] = Err("not a 2")
        >>> y: Result[int, str] = Err("late error")
        >>> x.or_(y)
        Err('late error')

        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[int, str] = Ok(100)
        >>> x.or_(y)
        Ok(2)
        """

    @abstractmethod
    def or_else(self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        """Calls `op` if the result is Err, otherwise returns returns the Ok
        value from self.

        This function can be used for control flow based on result values.

        Basic usage:
        >>> def sq(x: int) -> Result[int, int]: return Ok(x * x)
        ...
        >>> def err(x: int) -> Result[int, int]: return Err(x)
        ...
        >>> Ok(2).or_else(sq).or_else(sq)
        Ok(2)
        >>> Ok(2).or_else(err).or_else(sq)
        Ok(2)
        >>> Err(3).or_else(sq).or_else(err)
        Ok(9)
        >>> Err(3).or_else(err).or_else(err)
        Err(3)
        """

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Returns the contained Ok value or a provided default.

        Arguments passed to unwrap_or are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use unwrap_or_else,
        which is lazily evaluated.

        Basic usage:
        >>> default = 2
        >>> x: Result[int, str] = Ok(9)
        >>> x.unwrap_or(default)
        9

        >>> x: Result[int, str] = Err("error")
        >>> x.unwrap_or(default)
        2
        """

    @abstractmethod
    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """Returns the contained Ok value or computes it from a closure.

        Basic usage:
        >>> def count(x: str) -> int: return len(x)
        >>> Ok(2).unwrap_or_else(count)
        2
        >>> Err("foo").unwrap_or_else(count)
        3
        """

    @abstractmethod
    def expect(self, msg: str) -> T:
        """Returns the contained Ok value, consuming the `self` value.

        Raises an AssertionError if the value is an Err, with a message
        including the passed message, and the content of the Err.

        Basic usage:
        >>> x: Result[int, str] = Err("emergency failure")
        >>> x.expect("Testing expect")
        Traceback (most recent call last):
            ...
        AssertionError: Testing expect: 'emergency failure'
        """

    @abstractmethod
    def unwrap(self) -> T:
        """Returns the contained Ok value, consuming the `self` value.

        Because this function may panic, its use is generally discouraged.
        Instead, prefer to use pattern matching and handle the Err case
        explicitly, or call `unwrap_or`, `unwrap_or_else`, or
        `unwrap_or_default`.

        Raises AssertionError if the value is an Err, with a message provided by
        the Err's value.

        Basic usage:
        >>> x: Result[int, str] = Ok(2)
        >>> x.unwrap()
        2

        >>> x: Result[int, str] = Err("emergency failure")
        >>> x.unwrap()
        Traceback (most recent call last):
            ...
        AssertionError: emergency failure
        """

    @abstractmethod
    def expect_err(self, msg: str) -> E:
        """Returns the contained Err value.

        Raises AssertionError if the value is an Ok, with a message including
        the passed message, and the content of the Ok.

        Basic usage:
        >>> x: Result[int, str] = Ok(10)
        >>> x.expect_err("Testing expect_err")
        Traceback (most recent call last):
            ...
        AssertionError: Testing expect_err: 10
        """

    @abstractmethod
    def unwrap_err(self) -> E:
        """Returns the contained Err value, consuming the `self` value.

        Raises AssertionError if the value is an Ok, with a custom panic message
        provided by the Ok's value.

        >>> x: Result[int, str] = Ok(2)
        >>> x.unwrap_err()
        Traceback (most recent call last):
            ...
        AssertionError: 2

        >>> x: Result[int, str] = Err("emergency failure")
        >>> x.unwrap_err()
        'emergency failure'
        """


@dependent_ord("value")
class Ok(Result[T, E]):
    """Contains the success value."""

    __slots__ = ("value",)

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
        raise AssertionError(f"{msg}: {repr(self.value)}")

    def unwrap_err(self) -> E:
        raise AssertionError(self.value)

    def __repr__(self):
        return f"Ok({repr(self.value)})"

    def __eq__(self, other: Any):
        if type(self) is not type(other):
            return NotImplemented
        return self.value == other.value

    __hash__ = dependent_hash("value")


@dependent_ord("error")
class Err(Result[T, E]):
    """Contains the error value."""

    __slots__ = ("error",)

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
        raise AssertionError(f"{msg}: {repr(self.error)}")

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
