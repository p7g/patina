"""Optional values.

Type Option represents an optional value: every Option is either Some and
contains a value, or None\\_, and does not. Option types are very common in Rust
code, as they have a number of uses:

- Initial values
- Return values for functions that are not defined over their entire input range
  (partial functions)
- Return value for otherwise reporting simple errors, where None\\_ is returned on
  error
- Optional struct fields
- Struct fields that can be loaned or "taken"
- Optional function arguments
- Nullable pointers
- Swapping things out of difficult situations

Options are commonly paired with pattern matching to query the presence of a
value and take action, always accounting for the None\\_ case.

>>> def divide(numerator: float, denominator: float) -> Option[float]:
...     if denominator == 0.0:
...         return None\\_()
...     return Some(numerator / denominator)
...
>>> result = divide(2.0, 3.0)
>>>
>>> if isinstance(result, Some):
...     print(f"Result: {result.value}")
... else:
...     print(f"Cannot divide by 0")
...
Result: 0.6666666666666666

Examples
--------

Basic pattern matching on Option:

>>> msg = Some("howdy")
>>>
>>> if isinstance(msg, Some):
...     print(msg.value)
...
>>> unwrapped_msg = msg.unwrap_or("default message")
>>> unwrapped_msg
howdy

Initialize a result to None\\_ before a loop:

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
>>> # with we've just got `None\\_`
>>> name_of_biggest_animal = None\\_()
>>> size_of_biggest_animal = 0
>>> for big_thing in all_the_big_things:
...     if isinstance(big_thing, AnimalKingdom) \\
...             and big_thing.size > size_of_biggest_animal:
...         size_of_biggest_animal = big_thing.size
...         name_of_biggest_animal = Some(big_thing.name)
...
>>> if isinstance(name_of_biggest_animal, Some):
...     print(f"the biggest animal is {name_of_biggest_animal.value}")
... else:
...     print("there are no animals :(")
...
the biggest animal is blue whale
"""

from abc import ABC, abstractmethod
from typing import final, Callable, Generic, Iterator, Tuple, Type, TypeVar, Union

from .ref import Ref

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")

@final
class _nothing:
    pass


class Option(Generic[T], ABC):
    """The ``Option`` type. See the module-level documentation for more."""

    __slots__ = ('_value',)
    _value: Union[Type[_nothing], T]

    @abstractmethod
    def is_some(self) -> bool:
        """Returns ``True`` if the option is a Some value.

        >>> x: Option[int] = Some(2)
        >>> x.is_some()
        True
        >>> x: Option[int] = None_()
        >>> x.is_some()
        False
        """

    @abstractmethod
    def is_none(self) -> bool:
        """Returns ``True`` if the option is a None\\_ value.

        >>> x: Option[int] = Some(2)
        >>> x.is_none()
        False
        >>> x: Option[int] = None_()
        >>> x.is_none()
        True
        """

    @abstractmethod
    def expect(self, msg: str) -> T:
        """Returns the contained Some value.

        :raises AssertionError: Raised if the value is a None\\_ with a custom
            message provided by ``msg``.

        >>> x = Some("value")
        >>> x.expect("fruits are healthy")
        'value'
        >>> x: Option[str] = None_()
        >>> x.expect("fruits are healthy")
        Traceback (most recent call last):
            ...
        AssertionError: fruits are healthy
        """

    @abstractmethod
    def unwrap(self) -> T:
        """Returns the contained Some value.

        Because this function may panic, its use is generally discouraged.
        Instead, prefer to use pattern matching and handle the None\\_ case
        explicitly, or call ``unwrap_or``, ``unwrap_or_else``, or
        ``unwrap_or_default``.

        :raises AssertionError: Raised if the self value is None\\_.

        >>> x = Some("air")
        >>> x.unwrap()
        'air'
        >>> x: Option[str] = None_()
        >>> x.unwrap()
        Traceback (most recent call last):
            ...
        AssertionError: called `Option.unwrap` on a `None` value
        """

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Returns the contained Some value or a provided default.
        
        Arguments passed to ``unwrap_or`` are eagerly evaluated; if you are
        passing the result of a function call, it is recommended to use
        ``unwrap_or_else``, which is lazily evaluated.
        
        >>> Some("car").unwrap_or("bike")
        'car'
        >>> None_().unwrap_or("bike")
        'bike'
        """

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Returns the contained Some value or computes it from a closure.

        >>> k = 10
        >>> Some(4).unwrap_or_else(lambda: 2 * k)
        4
        >>> None_().unwrap_or_else(lambda: 2 * k)
        20
        """

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> 'Option[U]':
        """Maps an ``Option[T]`` to ``Option[U]`` by applying a function to a
        contained value.

        Converts an ``Option[str]`` into an ``Option[int]``:

        >>> maybe_some_string = Some("Hello, World!")
        >>> maybe_some_len = maybe_some_string.map(len)
        >>> maybe_some_len
        Some(13)
        """

    @abstractmethod
    def map_or(self, default: U, f: Callable[[T], U]) -> U:
        """Applies a function to the contained value (if any), or returns the
        provided default (if not).

        Arguments passed to ``map_or`` are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use ``map_or_else``,
        which is lazily evaluated.

        >>> x = Some("foo")
        >>> x.map_or(42, len)
        3
        >>> x: Option[str] = None_()
        >>> x.map_or(42, len)
        42
        """

    @abstractmethod
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

    @abstractmethod
    def ok_or(self, err: E) -> "Result[T, E]":
        """Transforms the ``Option[T]`` into a ``Result[T, E]``, mapping
        ``Some(v)`` to ``Ok(v)`` and ``None_`` to ``Err(err)``.

        Arguments passed to ``ok_or`` are eagerly evaluated; if you are passing
        the result of a function call, it is recommended to use ``ok_or_else``,
        which is lazily evaluated.

        >>> x = Some("foo")
        >>> x.ok_or(0)
        Ok('foo')
        >>> x: Option[str] = None_()
        >>> x.ok_or(0)
        Err(0)
        """

    @abstractmethod
    def ok_or_else(self, err: Callable[[], E]) -> "Result[T, E]":
        """Transforms the ``Option[T]`` into a ``Result[T, E]``, mapping
        ``Some(v)`` to ``Ok(v)`` and ``None_`` to ``Err(err())``.

        >>> x = Some("foo")
        >>> x.ok_or_else(lambda: 0)
        Ok('foo')
        >>> x: Option[str] = None_()
        >>> x.ok_or_else(lambda: 0)
        Err(0)
        """

    @abstractmethod
    def iter(self) -> Iterator[T]:
        """Returns an iterator over the possibly contained value.
        
        >>> x = Some(4)
        >>> next(x.iter())
        4
        >>> x = None_()
        >>> next(x.iter())
        Traceback (most recent call last):
            ...
        StopIteration
        """

    def __iter__(self):
        """Returns an iterator over the possibly contained value.
        
        >>> x = Some(4)
        >>> next(iter(x))
        4
        >>> x = None_()
        >>> next(iter(x))
        Traceback (most recent call last):
            ...
        StopIteration
        """
        return self.iter()

    @abstractmethod
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

    @abstractmethod
    def and_then(self, f: Callable[[T], U]) -> "Option[U]":
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

    @abstractmethod
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

    @abstractmethod
    def or_(self, optb: "Option[T]") -> "Option[T]":
        """Returns the option if it contains a value, otherwise returns
        ``optb``.
        
        Arguments passed to ``or`` are eagerly evaluated; if you are passing the
        result of a function call, it is recommended to use ``or_else``, which
        is lazily evaluated.

        >>> x = Some(2)
        >>> y = None_()
        >>> x.or_(y)
        Some(2)
        >>> x = None_()
        >>> y = Some(100)
        >>> x.or_(y)
        Some(100)
        >>> x = Some(2)
        >>> y = Some(100)
        >>> x.or_(y)
        Some(2)
        >>> x: Option[int] = None_()
        >>> y = None_()
        >>> x.or_(y)
        None_
        """

    @abstractmethod
    def or_else(self, f: Callable[[], T]) -> "Option[T]":
        """Returns the option if it contains a value, otherwise calls ``f`` and
        returns the result.

        >>> def nobody() -> Option[str]: return None_()
        ...
        >>> def vikings() -> Option[str]: return Some("vikings")
        ...
        >>> Some("barbarians").or_else(vikings)
        Some('barbarians')
        >>> None_().or_else(vikings)
        Some('vikings')
        >>> None_().or_else(nobody)
        None_
        """

    @abstractmethod
    def xor(self, optb: "Option[T]") -> "Option[T]":
        """Returns Some if exactly one of ``self``, ``optb`` is Some, otherwise
        returns ``None_``.

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

    @abstractmethod
    def get_or_insert(self, v: T) -> Ref[T]:
        """Inserts ``v`` into the option if it is ``None_``, then returns
        a reference to the contained value.

        >>> x = None_()
        >>> y = x.get_or_insert(5)
        >>> y.get()
        5
        >>> y.set(7)
        >>> x
        Some(7)
        """

    @abstractmethod
    def get_or_insert_with(self, f: Callable[[], T]) -> Ref[T]:
        """Inserts a value computed from ``f`` into the option if it is
        ``None_``, then returns a reference to the contained value.

        >>> x = None_()
        >>> y = x.get_or_insert_with(lambda: 5)
        >>> y.get()
        5
        >>> y.set(7)
        >>> x
        Some(7)
        """

    @abstractmethod
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

    @abstractmethod
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
        >>> x = None_()
        >>> old = x.replace(3)
        >>> x
        Some(3)
        >>> old
        None_()
        """

    @abstractmethod
    def zip(self, other: "Option[U]") -> "Option[Tuple[T, U]]":
        """Zips ``self`` with another ``Option``.

        If ``self`` is ``Some(s)`` and ``other`` is ``Some(o)``, this method
        returns ``Some((s, o))``. Otherwise, ``None_`` is returned.

        >>> x = Some(1)
        >>> y = Some("hi")
        >>> z = None_[int]()
        >>> x.zip(y)
        Some((1, "hi"))
        >>> x.zip(z)
        None_
        """


class Some(Option[T]):
    """Some value ``T``."""

    def __init__(self, value: T):
        self._value = value

    def is_some(self) -> bool:
        return True

    def __repr__(self):
        return f"Some({repr(self._value)})"


class None_(Option[T]):
    """No value."""

    def __init__(self):
        self._value = _nothing

    def is_some(self) -> bool:
        return False

    def __repr__(self):
        return "None_"


from .result import Result