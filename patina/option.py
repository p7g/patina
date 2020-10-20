"""Optional values.

Type Option represents an optional value: every Option is either
:meth:`Option.Some` and contains a value, or :meth:`Option.None_`, and does not.
Option types are very common in Rust code, as they have a number of uses:

- Initial values
- Return values for functions that are not defined over their entire input range
  (partial functions)
- Return value for otherwise reporting simple errors, where ``None_`` is
  returned on error
- Optional struct fields
- Struct fields that can be loaned or "taken"
- Optional function arguments
- Nullable pointers
- Swapping things out of difficult situations

Options are commonly paired with pattern matching to query the presence of a
value and take action, always accounting for the ``None_`` case.

>>> def divide(numerator: float, denominator: float) -> Option[float]:
...     if denominator == 0.0:
...         return None_()
...     return Some(numerator / denominator)
...
>>> result = divide(2.0, 3.0)
>>>
>>> if result.is_some():
...     print(f"Result: {result.unwrap()}")
... else:
...     print(f"Cannot divide by 0")
...
Result: 0.6666666666666666

Examples
--------

Basic pattern matching on :class:`Option`:

>>> msg = Some("howdy")
>>>
>>> if msg.is_some():
...     print(msg.unwrap())
...
howdy
>>> unwrapped_msg = msg.unwrap_or("default message")
>>> unwrapped_msg
'howdy'

Initialize a result to ``None_`` before a loop:

>>> from dataclasses import dataclass
>>>
>>> @dataclass
... class Kingdom:
...     size: int
...     name: str
...
>>> class PlantKingdom(Kingdom): pass
...
>>> class AnimalKingdom(Kingdom): pass
...
>>> all_the_big_things = [
...     PlantKingdom(250, "redwood"),
...     PlantKingdom(230, "noble fir"),
...     PlantKingdom(229, "sugar pine"),
...     AnimalKingdom(25, "blue whale"),
...     AnimalKingdom(19, "fin whale"),
...     AnimalKingdom(15, "north pacific right whale"),
... ]
>>>
>>> # We're going to search for the name of the biggest animal, but to start
>>> # with we've just got `None_`
>>> name_of_biggest_animal: Option[str] = None_()
>>> size_of_biggest_animal = 0
>>> for big_thing in all_the_big_things:
...     if isinstance(big_thing, AnimalKingdom) \\
...             and big_thing.size > size_of_biggest_animal:
...         size_of_biggest_animal = big_thing.size
...         name_of_biggest_animal = Some(big_thing.name)
...
>>> if name_of_biggest_animal.is_some():
...     print(f"the biggest animal is {name_of_biggest_animal.unwrap()}")
... else:
...     print("there are no animals :(")
...
the biggest animal is blue whale
"""

from typing import (
    Callable,
    Generic,
    Iterator,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from .ref import Ref
from ._utils import nothing, Nothing

__all__ = ("Option", "Some", "None_")

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


class Option(Generic[T]):
    """The ``Option`` type. See the :mod:`module-level documentation
    <result.option>` for more."""

    __slots__ = ("_value",)
    _value: Union[Nothing, T]

    def __init__(self, value: Union[Nothing, T] = nothing):
        """This constructor should not be called directly.

        Instead, use :meth:`Some` or :meth:`None_`
        """
        self._value = value

    def __bool__(self) -> bool:
        """Returns :obj:`True` if the option is a ``Some`` value, else :obj:,
        else :obj:`False`.
        >>> x: Option[int] = Some(0)
        >>> True if x else False
        True
        >>> y: Option[int] = None_()
        >>> True if y else False
        False
        """
        return self.is_some()

    def is_some(self) -> bool:
        """Returns :obj:`True` if the option is a ``Some`` value.

        >>> x: Option[int] = Some(2)
        >>> x.is_some()
        True
        >>> x: Option[int] = None_()
        >>> x.is_some()
        False
        """
        return self._value is not nothing

    def is_none(self) -> bool:
        """Returns :obj:`True` if the option is a ``None_`` value.

        >>> x: Option[int] = Some(2)
        >>> x.is_none()
        False
        >>> x: Option[int] = None_()
        >>> x.is_none()
        True
        """
        return self._value is nothing

    def expect(self, msg: str) -> T:
        """Returns the contained ``Some`` value.

        :raises AssertionError: Raised if the value is a ``None_``, with a
            custom message provided by ``msg``.

        >>> x = Some("value")
        >>> x.expect("fruits are healthy")
        'value'
        >>> x: Option[str] = None_()
        >>> x.expect("fruits are healthy")
        Traceback (most recent call last):
            ...
        AssertionError: fruits are healthy
        """
        if self._value is nothing:
            raise AssertionError(msg)
        return self._value

    def unwrap(self) -> T:
        """Returns the contained ``Some`` value.

        Because this function may panic, its use is generally discouraged.
        Instead, prefer to use pattern matching and handle the ``None_`` case
        explicitly, or call :meth:`unwrap_or` or :meth:`unwrap_or_else`.

        :raises AssertionError: Raised if the self value is ``None_``.

        >>> x = Some("air")
        >>> x.unwrap()
        'air'
        >>> x: Option[str] = None_()
        >>> x.unwrap()
        Traceback (most recent call last):
            ...
        AssertionError: called `Option.unwrap` on a `None_` value
        """
        if self._value is nothing:
            raise AssertionError("called `Option.unwrap` on a `None_` value")
        return self._value

    def unwrap_or(self, default: T) -> T:
        """Returns the contained ``Some`` value or a provided default.

        Arguments passed to ``unwrap_or`` are eagerly evaluated; if you are
        passing the result of a function call, it is recommended to use
        :meth:`unwrap_or_else`, which is lazily evaluated.

        >>> Some("car").unwrap_or("bike")
        'car'
        >>> Option[str].None_().unwrap_or("bike")
        'bike'
        """
        if self._value is nothing:
            return default
        return self._value

    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Returns the contained ``Some`` value or computes it from a closure.

        >>> k = 10
        >>> Some(4).unwrap_or_else(lambda: 2 * k)
        4
        >>> Option[int].None_().unwrap_or_else(lambda: 2 * k)
        20
        """
        if self._value is nothing:
            return f()
        return self._value

    def map(self, f: Callable[[T], U]) -> "Option[U]":
        """Maps an ``Option[T]`` to ``Option[U]`` by applying a function to a
        contained value.

        Converting an ``Option[str]`` into an ``Option[int]``:

        >>> maybe_some_string = Some("Hello, World!")
        >>> maybe_some_len = maybe_some_string.map(len)
        >>> maybe_some_len
        Some(13)
        """
        if self._value is nothing:
            return None_()
        return Some(f(self._value))

    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        """Applies a function to the contained value (if any), or returns the
        provided default (if not).

        Arguments passed to ``map_or`` are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use
        :meth:`map_or_else`, which is lazily evaluated.

        >>> x = Some("foo")
        >>> x.map_or(42, len)
        3
        >>> x: Option[str] = None_()
        >>> x.map_or(42, len)
        42
        """
        if self._value is nothing:
            return default
        return f(self._value)

    def map_or_else(self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        """Applies a function to the contained value (if any), or computes a
        default (if not).

        >>> k = 21
        >>>
        >>> x = Some("foo")
        >>> x.map_or_else(lambda: 2 * k, len)
        3
        >>> x: Option[str] = None_()
        >>> x.map_or_else(lambda: 2 * k, len)
        42
        """
        if self._value is nothing:
            return default()
        return f(self._value)

    def ok_or(self, err: E) -> "Result[T, E]":
        """Transforms the ``Option[T]`` into a :class:`Result[T, E]
        <result.result.Result>`, mapping ``Some(v)`` to ``Ok(v)`` and ``None_``
        to ``Err(err)``.

        Arguments passed to ``ok_or`` are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use
        :meth:`ok_or_else`, which is lazily evaluated.

        >>> x = Some("foo")
        >>> x.ok_or(0)
        Ok('foo')
        >>> x: Option[str] = None_()
        >>> x.ok_or(0)
        Err(0)
        """
        if self._value is nothing:
            return Result.Err(err)
        return Result.Ok(self._value)

    def ok_or_else(self, err: Callable[[], E]) -> "Result[T, E]":
        """Transforms the ``Option[T]`` into a :class:`Result[T, E]
        <result.result.Result>`, mapping ``Some(v)`` to ``Ok(v)`` and ``None_``
        to ``Err(err())``.

        >>> x = Some("foo")
        >>> x.ok_or_else(lambda: 0)
        Ok('foo')
        >>> x: Option[str] = None_()
        >>> x.ok_or_else(lambda: 0)
        Err(0)
        """
        if self._value is nothing:
            return Result.Err(err())
        return Result.Ok(self._value)

    def iter(self) -> Iterator[T]:
        """Returns an iterator over the possibly contained value.

        >>> x = Some(4)
        >>> next(x.iter())
        4
        >>> x: Option[int] = None_()
        >>> next(x.iter())
        Traceback (most recent call last):
            ...
        StopIteration
        """
        if self._value is not nothing:
            yield self._value

    def __iter__(self):
        """Returns an iterator over the possibly contained value.

        >>> x = Some(4)
        >>> next(iter(x))
        4
        >>> x: Option[int] = None_()
        >>> next(iter(x))
        Traceback (most recent call last):
            ...
        StopIteration
        """
        return self.iter()

    def and_(self, optb: "Option[U]") -> "Option[U]":
        """Returns ``None_`` if the option is ``None_``, otherwise returns
        ``optb``.

        >>> x = Some(2)
        >>> y: Option[str] = None_()
        >>> x.and_(y)
        None_
        >>> x: Option[int] = None_()
        >>> y = Some("foo")
        >>> x.and_(y)
        None_
        >>> x = Some(2)
        >>> y = Some("foo")
        >>> x.and_(y)
        Some('foo')
        >>> x: Option[int] = None_()
        >>> y: Option[str] = None_()
        >>> x.and_(y)
        None_
        """
        if self._value is nothing:
            return None_()
        return optb

    def and_then(self, f: Callable[[T], "Option[U]"]) -> "Option[U]":
        """Returns ``None_`` if the option is ``None_``, otherwise calls ``f``
        with the wrapped value and returns the result.

        Some languages call this operation flatmap.

        >>> def sq(x: int) -> Option[int]: return Some(x * x)
        ...
        >>> def nope(_: int) -> Option[int]: return None_()
        ...
        >>> Some(2).and_then(sq).and_then(sq)
        Some(16)
        >>> Some(2).and_then(sq).and_then(nope)
        None_
        >>> Some(2).and_then(nope).and_then(sq)
        None_
        >>> None_().and_then(sq).and_then(sq)
        None_
        """
        if self._value is nothing:
            return None_()
        return f(self._value)

    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        """Returns ``None_`` if the option is ``None_``, otherwise calls
        ``predicate`` with the wrapped value and returns:

        - ``Some(t)`` if ``predicate`` returns ``True`` (where ``t`` is the
          wrapped value, and
        - ``None_`` if ``predicate`` returns ``False``.

        This function works similar to :py:func:`python:filter`. You can
        imagine the ``Option[T]`` being an iterator over one or zero elements.
        ``filter()`` lets you decide which elements to keep.

        >>> def is_even(n: int) -> bool: return n % 2 == 0
        ...
        >>> None_().filter(is_even)
        None_
        >>> Some(3).filter(is_even)
        None_
        >>> Some(4).filter(is_even)
        Some(4)
        """
        if self._value is nothing or not predicate(self._value):
            return None_()
        return Some(self._value)

    def or_(self, optb: "Option[T]") -> "Option[T]":
        """Returns the option if it contains a value, otherwise returns
        ``optb``.

        Arguments passed to ``or`` are eagerly evaluated; if you are passing the
        result of a function call, it is recommended to use :meth:`or_else`,
        which is lazily evaluated.

        >>> x = Some(2)
        >>> y: Option[int] = None_()
        >>> x.or_(y)
        Some(2)
        >>> x: Option[int] = None_()
        >>> y = Some(100)
        >>> x.or_(y)
        Some(100)
        >>> x = Some(2)
        >>> y = Some(100)
        >>> x.or_(y)
        Some(2)
        >>> x: Option[int] = None_()
        >>> y: Option[int] = None_()
        >>> x.or_(y)
        None_
        """
        if self._value is nothing:
            return optb
        return Some(self._value)

    def or_else(self, f: Callable[[], "Option[T]"]) -> "Option[T]":
        """Returns the option if it contains a value, otherwise calls ``f`` and
        returns the result.

        >>> def nobody() -> Option[str]: return None_()
        ...
        >>> def vikings() -> Option[str]: return Some("vikings")
        ...
        >>> Some("barbarians").or_else(vikings)
        Some('barbarians')
        >>> Option[str].None_().or_else(vikings)
        Some('vikings')
        >>> Option[str].None_().or_else(nobody)
        None_
        """
        if self._value is nothing:
            return f()
        return Some(self._value)

    def xor(self, optb: "Option[T]") -> "Option[T]":
        """Returns ``Some`` if exactly one of ``self``, ``optb`` is ``Some``,
        otherwise returns ``None_``.

        >>> x = Some(2)
        >>> y: Option[int] = None_()
        >>> x.xor(y)
        Some(2)
        >>> x: Option[int] = None_()
        >>> y = Some(2)
        >>> x.xor(y)
        Some(2)
        >>> x = Some(2)
        >>> y = Some(2)
        >>> x.xor(y)
        None_
        >>> x: Option[int] = None_()
        >>> y: Option[int] = None_()
        >>> x.xor(y)
        None_
        """
        if self._value is nothing and optb._value is not nothing:
            return Some(optb._value)
        if self._value is not nothing and optb._value is nothing:
            return Some(self._value)
        return None_()

    def _make_value_ref(self) -> Ref[T]:
        def get_value() -> T:
            if self._value is nothing:
                raise AssertionError("Reading reference to None_ value")
            return self._value

        def set_value(value: T):
            if self._value is nothing:
                raise AssertionError("Writing to reference to None_ value")
            self._value = value

        return Ref(get_value, set_value)

    def get_or_insert(self, v: T) -> Ref[T]:
        """Inserts ``v`` into the option if it is ``None_``, then returns
        a reference to the contained value.

        >>> x: Option[int] = None_()
        >>> y = x.get_or_insert(5)
        >>> y.get()
        5
        >>> y.set(7)
        >>> x
        Some(7)
        """
        if self._value is nothing:
            self._value = v
        return self._make_value_ref()

    def get_or_insert_with(self, f: Callable[[], T]) -> Ref[T]:
        """Inserts a value computed from ``f`` into the option if it is
        ``None_``, then returns a reference to the contained value.

        >>> x: Option[int] = None_()
        >>> y = x.get_or_insert_with(lambda: 5)
        >>> y.get()
        5
        >>> y.set(7)
        >>> x
        Some(7)
        """
        if self._value is nothing:
            self._value = f()
        return self._make_value_ref()

    def take(self) -> "Option[T]":
        """Takes the value out of the option, leaving a ``None_`` in its place.

        >>> x = Some(2)
        >>> y = x.take()
        >>> x
        None_
        >>> y
        Some(2)
        >>> x: Option[int] = None_()
        >>> y = x.take()
        >>> x
        None_
        >>> y
        None_
        """
        if self._value is nothing:
            return None_()
        value, self._value = self._value, nothing
        return Some(value)

    def replace(self, value: T) -> "Option[T]":
        """Replaces the actual value in the option by the value given in
        parameter, returning the old value if present, leaving a ``Some`` in its
        place without deinitializing either one.

        >>> x = Some(2)
        >>> old = x.replace(5)
        >>> x
        Some(5)
        >>> old
        Some(2)
        >>> x = Option[int].None_()
        >>> old = x.replace(3)
        >>> x
        Some(3)
        >>> old
        None_
        """
        old_value, self._value = self._value, value
        if old_value is nothing:
            return None_()
        return Some(old_value)

    def zip(self, other: "Option[U]") -> "Option[Tuple[T, U]]":
        """Zips ``self`` with another :class:`Option`.

        If ``self`` is ``Some(s)`` and ``other`` is ``Some(o)``, this method
        returns ``Some((s, o))``. Otherwise, ``None_`` is returned.

        >>> x = Some(1)
        >>> y = Some("hi")
        >>> z = Option[int].None_()
        >>> x.zip(y)
        Some((1, 'hi'))
        >>> x.zip(z)
        None_
        """
        if self._value is nothing or other._value is nothing:
            return None_()
        return Some((self._value, other._value))

    def __repr__(self):
        if self._value is nothing:
            return "None_"
        return f"Some({repr(self._value)})"

    @classmethod
    def Some(cls, value: T) -> "Option[T]":
        """Some value ``T``"""
        return cls(value)

    @classmethod
    def None_(cls) -> "Option[T]":
        """No value"""
        return cls()

    @classmethod
    def from_optional(cls, opt: Optional[T]) -> "Option[T]":
        """Get an ``Option[T]`` from an :class:`Optional[T] <Optional>`.

        If ``opt`` is :obj:`None`, return :meth:`None_`, otherwise return
        :meth:`Some(obj) <Some>`. This does not come from Rust's API.

        >>> from typing import Optional
        >>> x: Optional[int] = None
        >>> Option.from_optional(x)
        None_
        >>> x: Optional[int] = 42
        >>> Option.from_optional(x)
        Some(42)
        """
        if opt is None:
            return cls.None_()
        return cls.Some(opt)


Some = Option.Some
None_ = Option.None_


from .result import Result  # noqa E402
