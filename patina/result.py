"""Error handling with the Result type.

:class:`Result[T, E] <Result>` is the type used for returning and propagating
errors. It is an enum with the variants, :meth:`Ok(T) <Ok>`, representing
success and containing a value, and :meth:`Err(E) <Err>`, representing error and
containing an error value.

Examples
--------

A simple function returning :class:`Result` might be defined and used like so:

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
>>> if version.is_ok():
...     print(f"working with version: {version.unwrap()}")
... else:
...     print(f"error parsing header: {version.unwrap_err()}")
...
working with version: Version.version_1

Pattern matching on :class:`Result`\\s is clear and straightforward for simple
cases (in Rust), but ``Result`` comes with some convenience methods that make
working with it more succinct.

>>> good_result: Result[int, int] = Ok(10)
>>> bad_result: Result[int, int] = Err(10)
>>>
>>> # The `is_ok` and `is_err` methods do what they say.
>>> good_result.is_ok() and not good_result.is_err()
True
>>> bad_result.is_err() and not bad_result.is_ok()
True
>>>
>>> # `map` consumes the `Result` and produces another.
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

import enum
from typing import Callable, Generic, Iterator, TypeVar, Union
from typing_extensions import final

from .option import Option
from ._utils import dependent_hash, dependent_ord, nothing, Nothing

__all__ = ("Result", "Ok", "Err")

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


@final
class _ResultState(enum.Enum):
    ok = enum.auto()
    err = enum.auto()


def _result_value_attr(r: "Result[T, E]") -> str:
    return "_left" if r._state is _ResultState.err else "_right"


@dependent_ord(_result_value_attr)
class Result(Generic[T, E]):
    """``Result`` is a type that represents either success (:meth:`Ok`) or
    failure (:meth:`Err`).
    """

    __slots__ = ("_state", "_left", "_right")
    _state: _ResultState
    _left: E
    _right: T

    def __init__(
        self,
        *,
        left: Union[Nothing, E] = nothing,
        right: Union[Nothing, T] = nothing,
    ):
        """This constructor should not be called directly.

        Instead, use :meth:`Ok` or :meth:`Err`.
        """
        if left is nothing and right is not nothing:
            self._state = _ResultState.ok
            self._right = right
        elif left is not nothing and right is nothing:
            self._state = _ResultState.err
            self._left = left
        else:
            raise AssertionError(
                "One and only one of `left` and `right` must be supplied to "
                "Result.__init__"
            )

    def is_ok(self) -> bool:
        """Returns :obj:`True` if the result is :meth:`Ok`.

        Basic usage:

        >>> x: Result[int, str] = Ok(-3)
        >>> x.is_ok()
        True
        >>>
        >>> x: Result[int, str] = Err("Some error message")
        >>> x.is_ok()
        False
        """
        return self._state is _ResultState.ok

    def is_err(self) -> bool:
        """Returns :obj:`True` if the result is :meth:`Err`.

        Basic usage:

        >>> x: Result[int, str] = Ok(-3)
        >>> x.is_err()
        False
        >>>
        >>> x: Result[int, str] = Err("Some error message")
        >>> x.is_err()
        True
        """
        return self._state is _ResultState.err

    def ok(self) -> Option[T]:
        """Converts from ``Result[T, E]`` to :class:`Option[T]
        <result.option.Option>`.

        Converts ``self`` into ``Option[T]``, discarding the error, if any.

        Basic usage:

        >>> x: Result[int, str] = Ok(2)
        >>> x.ok()
        Some(2)
        >>>
        >>> x: Result[int, str] = Err("Nothing here")
        >>> x.ok()
        None_
        """
        if self._state is _ResultState.err:
            return Option.None_()
        return Option.Some(self._right)

    def err(self) -> Option[E]:
        """Converts from ``Result[T, E]`` to :class:`Option[E]
        <result.option.Option>`.

        Converts ``self`` into ``Option[E]``, discarding the success value, if
        any.

        Basic usage:

        >>> x: Result[int, str] = Ok(2)
        >>> x.err()
        None_
        >>>
        >>> x: Result[int, str] = Err("Nothing here")
        >>> x.err()
        Some('Nothing here')
        """
        if self._state is _ResultState.ok:
            return Option.None_()
        return Option.Some(self._left)

    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        """Maps a ``Result[T, E]`` to ``Result[U, E]`` by applying a function to
        a contained :meth:`Ok` value, leaving an :meth:`Err` value untouched.

        This function can be used to compose the results of two functions.

        Printing the numbers on each line of a string multiplied by two:

        >>> def try_parse(s: str) -> Result[int, ValueError]:
        ...     try:
        ...         return Ok(int(s))
        ...     except ValueError as e:
        ...         return Err(e)
        ...
        >>> line = "1\\n2\\n3\\n4\\n5\\n"
        >>> for num in line.splitlines():
        ...     result = try_parse(num).map(lambda i: i * 2)
        ...     if result.is_ok():
        ...         print(result.unwrap())
        2
        4
        6
        8
        10
        """
        if self._state is _ResultState.err:
            return Err(self._left)
        return Ok(op(self._right))

    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        """Applies a function to the contained value (if :meth:`Ok`), or returns
        the provided default (if :meth:`Err`).

        Arguments passed to ``map_or`` are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use
        :meth:`map_or_else`, which is lazily evaluated.

        >>> x: Result[str, str] = Ok("foo")
        >>> x.map_or(42, lambda v: len(v))
        3
        >>>
        >>> x: Result[str, str] = Err("bar")
        >>> x.map_or(42, lambda v: len(v))
        42
        """
        if self._state is _ResultState.err:
            return default
        return f(self._right)

    def map_or_else(self, default: Callable[[E], U], f: Callable[[T], U]) -> U:
        """Maps a ``Result[T, E]`` to ``U`` by applying a function to a
        contained :meth:`Ok` value, or a fallback function to a contained
        :meth:`Err` value.

        This function can be used to unpack a successful result while handling
        an error.

        Basic usage:

        >>> k = 21
        >>>
        >>> x: Result[str, str] = Ok("foo")
        >>> x.map_or_else(lambda e: k * 2, lambda v: len(v))
        3
        >>>
        >>> x: Result[str, str] = Err("foo")
        >>> x.map_or_else(lambda e: k * 2, lambda v: len(v))
        42
        """
        if self._state is _ResultState.err:
            return default(self._left)
        return f(self._right)

    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        """Maps a ``Result[T, E]`` to ``Result[T, F]`` by applying a function to
        a contained :meth:`Err` value, leaving an :meth:`Ok` value untouched.

        This function can be used to pass through a successful result while
        handling an error.

        Basic usage:

        >>> def stringify(x: int) -> str:
        ...     return f"error code: {x}"
        ...
        >>> x: Result[int, int] = Ok(2)
        >>> x.map_err(stringify)
        Ok(2)
        >>>
        >>> x: Result[int, int] = Err(13)
        >>> x.map_err(stringify)
        Err('error code: 13')
        """
        if self._state is _ResultState.ok:
            return Ok(self._right)
        return Err(op(self._left))

    def iter(self) -> Iterator[T]:
        """Returns an iterator over the possibly contained value.

        The iterator yields one value if the reusult is :meth:`Ok`, otherwise
        none.

        Basic usage:

        >>> x: Result[int, str] = Ok(7)
        >>> next(x.iter())
        7
        >>>
        >>> x: Result[int, str] = Err("nothing!")
        >>> next(x.iter())
        Traceback (most recent call last):
            ...
        StopIteration
        """
        if self._state is _ResultState.ok:
            yield self._right

    def __iter__(self) -> Iterator[T]:
        """Returns an iterator over the possibly contained value.

        The iterator yields one value if the reusult is :meth:`Ok`, otherwise
        none.

        Basic usage:

        >>> x: Result[int, str] = Ok(7)
        >>> next(iter(x))
        7
        >>>
        >>> x: Result[int, str] = Err("nothing!")
        >>> next(iter(x))
        Traceback (most recent call last):
            ...
        StopIteration
        """
        return self.iter()

    def and_(self, res: "Result[U, E]") -> "Result[U, E]":
        """Returns ``res`` if the result is :meth:`Ok`, otherwise returns the
        :meth:`Err` value of ``self``.

        Basic usage:

        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[str, str] = Err("late error")
        >>> x.and_(y)
        Err('late error')
        >>>
        >>> x: Result[int, str] = Err("early error")
        >>> y: Result[str, str] = Ok("foo")
        >>> x.and_(y)
        Err('early error')
        >>>
        >>> x: Result[int, str] = Err("not a 2")
        >>> y: Result[str, str] = Err("late error")
        >>> x.and_(y)
        Err('not a 2')
        >>>
        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[str, str] = Ok("different result type")
        >>> x.and_(y)
        Ok('different result type')
        """
        if self._state is _ResultState.ok:
            return res
        return Err(self._left)

    def and_then(self, op: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Calls ``op`` if the result is :meth:`Ok`, otherwise returns the
        :meth:`Err` value of ``self``.

        This function can be used for control flow based on :class:`Result`
        values.

        Basic usage:

        >>> def sq(x: int) -> Result[int, int]: return Ok(x * x)
        ...
        >>> def err(x: int) -> Result[int, int]: return Err(x)
        ...
        >>> Result[int, int].Ok(2).and_then(sq).and_then(sq)
        Ok(16)
        >>> Result[int, int].Ok(2).and_then(sq).and_then(err)
        Err(4)
        >>> Result[int, int].Ok(2).and_then(err).and_then(sq)
        Err(2)
        >>> Err(3).and_then(sq).and_then(sq)
        Err(3)
        """
        if self._state is _ResultState.err:
            return Err(self._left)
        return op(self._right)

    def or_(self, res: "Result[T, F]") -> "Result[T, F]":
        """Returns ``res`` if the result is :meth:`Err`, otherwise returns the
        :meth:`Ok` result of self.

        Arguments passed to or are eagerly evaluated; if you are passing the
        result of a function call, it is recommended to use :meth:`or_else`,
        which is lazily evaluated.

        Basic usage:

        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[int, str] = Err("late error")
        >>> x.or_(y)
        Ok(2)
        >>>
        >>> x: Result[int, str] = Err("early error")
        >>> y: Result[int, str] = Ok(2)
        >>> x.or_(y)
        Ok(2)
        >>>
        >>> x: Result[int, str] = Err("not a 2")
        >>> y: Result[int, str] = Err("late error")
        >>> x.or_(y)
        Err('late error')
        >>>
        >>> x: Result[int, str] = Ok(2)
        >>> y: Result[int, str] = Ok(100)
        >>> x.or_(y)
        Ok(2)
        """
        if self._state is _ResultState.ok:
            return Ok(self._right)
        return res

    def or_else(self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        """Calls ``op`` if the result is :meth:`Err`, otherwise returns returns
        the :meth:`Ok` value from self.

        This function can be used for control flow based on result values.

        Basic usage:

        >>> def sq(x: int) -> Result[int, int]: return Ok(x * x)
        ...
        >>> def err(x: int) -> Result[int, int]: return Err(x)
        ...
        >>> Result[int, int].Ok(2).or_else(sq).or_else(sq)
        Ok(2)
        >>> Result[int, int].Ok(2).or_else(err).or_else(sq)
        Ok(2)
        >>> Result[int, int].Err(3).or_else(sq).or_else(err)
        Ok(9)
        >>> Result[int, int].Err(3).or_else(err).or_else(err)
        Err(3)
        """
        if self._state is _ResultState.ok:
            return Ok(self._right)
        return op(self._left)

    def unwrap_or(self, default: T) -> T:
        """Returns the contained :meth:`Ok` value or a provided default.

        Arguments passed to unwrap_or are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use
        :meth:`unwrap_or_else`, which is lazily evaluated.

        Basic usage:

        >>> default = 2
        >>> x: Result[int, str] = Ok(9)
        >>> x.unwrap_or(default)
        9
        >>>
        >>> x: Result[int, str] = Err("error")
        >>> x.unwrap_or(default)
        2
        """
        if self._state is _ResultState.err:
            return default
        return self._right

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        """Returns the contained :meth:`Ok` value or computes it from a closure.

        Basic usage:

        >>> def count(x: str) -> int: return len(x)
        ...
        >>> Ok(2).unwrap_or_else(count)
        2
        >>> Result[int, str].Err("foo").unwrap_or_else(count)
        3
        """
        if self._state is _ResultState.err:
            return op(self._left)
        return self._right

    def expect(self, msg: str) -> T:
        """Returns the contained :meth:`Ok` value.

        :raises AssertionError: Raised if the value is an :meth:`Err`, with a
            message including the passed message and the content of the ``Err``.

        Basic usage:

        >>> x: Result[int, str] = Err("emergency failure")
        >>> x.expect("Testing expect")
        Traceback (most recent call last):
            ...
        AssertionError: Testing expect: 'emergency failure'
        """
        if self._state is _ResultState.err:
            raise AssertionError(f"{msg}: {repr(self._left)}")
        return self._right

    def unwrap(self) -> T:
        """Returns the contained :meth:`Ok` value, consuming the ``self`` value.

        Because this function may panic, its use is generally discouraged.
        Instead, prefer to use pattern matching and handle the Err case
        explicitly, or call :meth:`unwrap_or` or :meth:`unwrap_or_else`.

        :raises AssertionError: Raised if the value is an :meth:`Err`, with a
            message provided by the ``Err``\\'s value.

        Basic usage:

        >>> x: Result[int, str] = Ok(2)
        >>> x.unwrap()
        2
        >>>
        >>> x: Result[int, str] = Err("emergency failure")
        >>> x.unwrap()
        Traceback (most recent call last):
            ...
        AssertionError: emergency failure
        """
        if self._state is _ResultState.err:
            raise AssertionError(self._left)
        return self._right

    def expect_err(self, msg: str) -> E:
        """Returns the contained :meth:`Err` value.

        :raises AssertionError: Raised if the value is an :meth:`Ok`, with a
            message including the passed message and the content of the ``Ok``.

        Basic usage:

        >>> x: Result[int, str] = Ok(10)
        >>> x.expect_err("Testing expect_err")
        Traceback (most recent call last):
            ...
        AssertionError: Testing expect_err: 10
        """
        if self._state is _ResultState.ok:
            raise AssertionError(f"{msg}: {repr(self._right)}")
        return self._left

    def unwrap_err(self) -> E:
        """Returns the contained :meth:`Err` value.

        :raises AssertionError: Raised if the value is an :meth:`Ok`, with a
            custom message provided by the ``Ok``\\'s value.

        >>> x: Result[int, str] = Ok(2)
        >>> x.unwrap_err()
        Traceback (most recent call last):
            ...
        AssertionError: 2
        >>>
        >>> x: Result[int, str] = Err("emergency failure")
        >>> x.unwrap_err()
        'emergency failure'
        """
        if self._state is _ResultState.ok:
            raise AssertionError(self._right)
        return self._left

    __hash__ = dependent_hash(_result_value_attr)

    def __repr__(self):
        if self._state is _ResultState.ok:
            return f"Ok({repr(self._right)})"
        return f"Err({repr(self._left)})"

    @classmethod
    def Ok(cls, value: T) -> "Result[T, E]":
        """Contains the success value"""
        return cls(right=value)

    @classmethod
    def Err(cls, error: E) -> "Result[T, E]":
        """Contains the error value"""
        return cls(left=error)


Ok = Result.Ok
Err = Result.Err
