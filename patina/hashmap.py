"""A hash map that wraps Python's ``dict`` with Rust's HashMap API.

Examples
--------

>>> from patina import HashMap
>>>
>>> book_reviews: HashMap[str, str] = HashMap()  # or HashMap.new()
>>>
>>> # Review some books.
>>> book_reviews.insert(
...     "Adventures of Huckleberry Finn",
...     "My favorite book.",
... )
None_
>>> book_reviews.insert(
...     "Grimms' Fairy Tales",
...     "Masterpiece.",
... )
None_
>>> book_reviews.insert(
...     "Pride and Prejudice",
...     "Very enjoyable.",
... )
None_
>>> book_reviews.insert(
...     "The Adventures of Sherlock Holmes",
...     "Eye lyked it alot.",
... )
None_
>>>
>>> # Check for a specific one.
>>> if not book_reviews.contains_key("Les Misérables"):
...     print(
...         "We've got {} reviews, but Les Misérables ain't one.".format(
...             len(book_reviews)
...         )
...     )
...
We've got 4 reviews, but Les Misérables ain't one.
>>>
>>> # oops, this review has a lot of spelling mistakes, let's deleted it.
>>> book_reviews.remove("The Adventures of Sherlock Holmes")
Some('Eye lyked it alot.')
>>>
>>> # Look up the values associated with some keys.
>>> to_find = ["Pride and Prejudice", "Alice's Adventure in Wonderland"]
>>> for book in to_find:
...     review = book_reviews.get(book)
...     if review.is_some():
...         print("{}: {}".format(book, review.unwrap()))
...     else:
...         print("{} is unreviewed.".format(book))
...
Pride and Prejudice: Very enjoyable.
Alice's Adventure in Wonderland is unreviewed.
>>>
>>> # Look up the value for a key (will raise KeyError if the key is not found).
>>> print("Review for Jane: {}".format(book_reviews["Pride and Prejudice"]))
Review for Jane: Very enjoyable.
>>>
>>> # Iterate over everything.
>>> for book, review in book_reviews:
...     print('{}: "{}"'.format(book, review))
...
Adventures of Huckleberry Finn: "My favorite book."
Grimms' Fairy Tales: "Masterpiece."
Pride and Prejudice: "Very enjoyable."

:class:`HashMap` also implements an ``Entry API``, which allows for more complex
methods of getting, setting, updating, and removing keys and their values:

>>> from patina import HashMap
>>>
>>> player_stats = HashMap[str, int]()
>>>
>>> def random_stat_buff() -> int:
...     # could actually return some random value here - let's just return some
...     # fixed value for now
...     return 42
...
>>> # insert a key only if it doesn't exist
>>> player_stats.entry("health").or_insert(100)
Ref(100)
>>>
>>> # insert a key using a function that provides a new value only if it doesn't
>>> # already exist
>>> player_stats.entry("defence").or_insert_with(random_stat_buff)
Ref(42)
>>>
>>> # update a key, guarding against the key possibly not being set
>>> stat = player_stats.entry("attack").or_insert(100)
>>> stat.modify(lambda stat: stat + random_stat_buff())
Ref(142)

:class:`HashMap` can be used with any key type that is ``Hashable``.

>>> from dataclasses import dataclass
>>> from patina import HashMap
>>>
>>> @dataclass(frozen=True)  # frozen so dataclass will add a __hash__ impl
... class Viking:
...     name: str
...     country: str
...
>>> # Use a HashMap to store the vikings' health points.
>>> vikings = HashMap[Viking, int]()
>>>
>>> vikings.insert(Viking("Einar", "Norway"), 25)
None_
>>> vikings.insert(Viking("Olaf", "Denmark"), 24)
None_
>>> vikings.insert(Viking("Harald", "Iceland"), 12)
None_
>>>
>>> # Print the status of the vikings.
>>> for viking, health in vikings:
...     print(repr(viking), "has", health, "hp")
...
Viking(name='Einar', country='Norway') has 25 hp
Viking(name='Olaf', country='Denmark') has 24 hp
Viking(name='Harald', country='Iceland') has 12 hp

A :class:`HashMap` with fixed list of elements can be initialized from a list:

>>> from patina import HashMap
>>>
>>> timber_resources = HashMap.from_iter(
...     [("Norway", 100), ("Denmark", 50), ("Iceland", 10)]
... )
>>> timber_resources
HashMap({'Norway': 100, 'Denmark': 50, 'Iceland': 10})
"""


import typing as t
from abc import ABC, abstractmethod
from functools import partial

from .option import Option, None_, Some
from .ref import Ref

__all__ = ["Entry", "OccupiedEntry", "VacantEntry", "HashMap"]

K = t.TypeVar("K", bound=t.Hashable)
V = t.TypeVar("V")
_nothing = object()


class Entry(ABC, t.Generic[K, V]):
    """A view into a single entry into a map, which may either be vacant or
    occupied.

    This class is constructed from the :func:`entry` method on :class:`HashMap`.
    """

    def __init__(self, table: "HashMap[K, V]", key: K):
        self._key = key
        self._table = table

    def or_insert(self, default: V) -> Ref[V]:
        """Ensures a value is in the entry by inserting the default if empty,
        and returns a mutable reference to the value in the entry.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert(3)
        Ref(3)
        >>> map["poneyland"]
        3
        >>> map.entry("poneyland").or_insert(10).modify(lambda v: v * 2)
        Ref(6)
        >>> map["poneyland"]
        6
        """
        return self.or_insert_with(lambda: default)

    @abstractmethod
    def or_insert_with(self, default: t.Callable[[], V]) -> Ref[V]:
        """Ensures a value is in the entry by inserting the result of the
        default function if empty, and returns a mutable reference to the value
        in the entry.

        >>> map = HashMap[str, str]()
        >>> s = "hoho"
        >>> map.entry("poneyland").or_insert_with(lambda: s)
        Ref('hoho')
        >>> map["poneyland"]
        'hoho'
        """

    def or_insert_with_key(self, default: t.Callable[[K], V]) -> Ref[V]:
        """Ensures a value is in the entry by inserting, if empty, the result of
        the default function. This method allows for generating key-derived
        values for insertion by providing the default function a reference to
        the key that was moved during the ``.entry(key)`` method call (not
        applicable to Python).

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert_with_key(len)
        Ref(9)
        >>> map["poneyland"]
        9
        """
        return self.or_insert_with(partial(default, self._key))

    def key(self) -> K:
        """Returns a reference to this entry's key.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").key()
        'poneyland'
        """
        return self._key

    @abstractmethod
    def and_modify(self, f: t.Callable[[Ref[V]], None]) -> "Entry[K, V]":
        r"""Provides in-place mutable access to an occupied entry before any
        potential inserts into the map.

        >>> from patina import Ref
        >>>
        >>> map = HashMap[str, int]()
        >>>
        >>> def add_one(ref: Ref[int]):
        ...     ref.modify(lambda val: val + 1)
        ...
        >>>
        >>> map.entry("poneyland") \
        ...     .and_modify(add_one) \
        ...     .or_insert(42)
        Ref(42)
        >>> map["poneyland"]
        42
        >>>
        >>> map.entry("poneyland") \
        ...     .and_modify(add_one) \
        ...     .or_insert(42)
        Ref(43)
        >>> map["poneyland"]
        43
        """


class OccupiedEntry(Entry[K, V]):
    """A view into an occupied entry in a :class:`HashMap`. It is part of the
    :class:`Entry` class hierarchy."""

    __match_args__ = ("_key", "_val")

    def _make_value_ref(self) -> Ref[V]:
        return self._table._make_value_ref(self._key)

    def or_insert_with(self, default: t.Callable[[], V]) -> Ref[V]:
        return self._make_value_ref()

    def and_modify(self, f: t.Callable[[Ref[V]], None]) -> Entry[K, V]:
        f(self._make_value_ref())
        return self

    def remove_entry(self) -> t.Tuple[K, V]:
        """Remove the entry from the map.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert(12)
        Ref(12)
        >>> o = map.entry("poneyland")
        >>> if isinstance(o, OccupiedEntry):
        ...     o.remove_entry()
        ...
        ('poneyland', 12)
        >>> "poneyland" in map
        False
        """
        return self._table.remove_entry(self._key).unwrap()

    def get(self) -> V:
        """Gets a reference to the value in the entry.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert(12)
        Ref(12)
        >>>
        >>> o = map.entry("poneyland")
        >>> if isinstance(o, OccupiedEntry):
        ...     print(o.get())
        ...
        12
        """
        return self._table[self._key]

    _val = property(get)

    def get_mut(self) -> Ref[V]:
        """Gets a mutable reference to the value in the entry.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert(12)
        Ref(12)
        >>>
        >>> map["poneyland"]
        12
        >>> o = map.entry("poneyland")
        >>> if isinstance(o, OccupiedEntry):
        ...     o.get_mut().modify(lambda v: v + 10)
        ...     o.get_mut().modify(lambda v: v + 2)
        ...
        Ref(22)
        Ref(24)
        >>> map["poneyland"]
        24
        """
        return self._make_value_ref()

    def insert(self, value: V) -> V:
        """Sets the value of the entry, and returns the entry's old value.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert(12)
        Ref(12)
        >>>
        >>> o = map.entry("poneyland")
        >>> if isinstance(o, OccupiedEntry):
        ...     o.insert(15)
        ...
        12
        >>> map["poneyland"]
        15
        """
        return self._table.insert(self._key, value).unwrap()

    def remove(self) -> V:
        """Takes the value out of the entry, and returns it.

        >>> map = HashMap[str, int]()
        >>> map.entry("poneyland").or_insert(12)
        Ref(12)
        >>>
        >>> o = map.entry("poneyland")
        >>> if isinstance(o, OccupiedEntry):
        ...     o.remove()
        ...
        12
        >>> "poneyland" in map
        False
        """
        return self._table.remove(self._key).unwrap()

    def __repr__(self):
        return f"OccupiedEntry(key={self._key!r}, value={self.get()!r})"


class VacantEntry(Entry[K, V]):
    """A view into a vacant entry in :class:`HashMap`. It is part of the
    :class:`Entry` class hierarchy."""

    __match_args__ = ("_key",)

    def or_insert_with(self, default: t.Callable[[], V]) -> Ref[V]:
        self._table.insert(self._key, default())
        return self._table._make_value_ref(self._key)

    def insert(self, value: V) -> Ref[V]:
        """Sets the value of the entry with the :class:`VacantEntry`'s key, and
        returns a mutable reference to it.

        >>> map = HashMap[str, int]()
        >>> o = map.entry("poneyland")
        >>> if isinstance(o, VacantEntry):
        ...     o.insert(37)
        ...
        Ref(37)
        >>> map["poneyland"]
        37
        """
        return self.or_insert(value)

    def and_modify(self, f: t.Callable[[Ref[V]], None]) -> Entry[K, V]:
        return self

    def __repr__(self):
        return f"VacantEntry(key={self._key!r})"


class HashMap(t.Generic[K, V]):
    _dict: t.Dict[K, V]

    # Allow matching like HashMap({"key": value})
    __match_args__ = ("_dict",)

    def __init__(self, dct: t.Optional[t.Dict[K, V]] = None):
        """Creates an empty :class:`HashMap`.

        >>> HashMap[str, int]()
        HashMap({})
        """
        self._dict = dct or {}

    @classmethod
    def new(cls):
        """Creates an empty :class:`HashMap`.

        >>> HashMap[str, int].new()
        HashMap({})
        """
        return cls()

    def keys(self) -> t.Iterable[K]:
        """An iterator visiting all keys in arbitrary order. The iterator
        element type is ``K``.

        >>> map = HashMap[str, int]()
        >>> map.insert("a", 1)
        None_
        >>> map.insert("b", 2)
        None_
        >>> map.insert("c", 3)
        None_
        >>>
        >>> for key in map.keys():
        ...     print(key)
        ...
        a
        b
        c
        """
        return self._dict.keys()

    def values(self) -> t.Iterable[V]:
        """An iterator visiting all values in arbitrary order. The iterator
        element type is ``V``.

        >>> map = HashMap[str, int]()
        >>> map.insert("a", 1)
        None_
        >>> map.insert("b", 2)
        None_
        >>> map.insert("c", 3)
        None_
        >>>
        >>> for val in map.values():
        ...     print(val)
        ...
        1
        2
        3
        """
        return self._dict.values()

    def _make_value_ref(self, key: K) -> Ref[V]:
        def set_value(val: V) -> None:
            self._dict[key] = val

        return Ref(lambda: self._dict[key], set_value)

    def values_mut(self) -> t.Iterable[Ref[V]]:
        """An iterator visiting all values mutably in arbitrary order. The
        iterator element type is ``Ref[V]``.

        >>> map = HashMap[str, int]()
        >>> map.insert("a", 1)
        None_
        >>> map.insert("b", 2)
        None_
        >>> map.insert("c", 3)
        None_
        >>>
        >>> for val in map.values_mut():
        ...     val.modify(lambda v: v + 10)
        ...
        Ref(11)
        Ref(12)
        Ref(13)
        >>> for val in map.values():
        ...     print(val)
        ...
        11
        12
        13
        """
        for key in self._dict:
            yield self._make_value_ref(key)

    def iter(self) -> t.Iterable[t.Tuple[K, V]]:
        """An iterator visiting all key-value pairs in arbitrary order. The
        iterator element type is ``Tuple[K, V]``.

        Equivalent to ``iter(map)``.

        >>> map = HashMap[str, int]()
        >>> map.insert("a", 1)
        None_
        >>> map.insert("b", 2)
        None_
        >>> map.insert("c", 3)
        None_
        >>>
        >>> for key, val in map.iter():
        ...     print("key:", key, "val:", val)
        ...
        key: a val: 1
        key: b val: 2
        key: c val: 3
        """
        return iter(self)

    def __iter__(self):
        """An iterator visiting all key-value pairs in arbitrary order. The
        iterator element type is ``Tuple[K, V]``.

        >>> map = HashMap[str, int]()
        >>> map.insert("a", 1)
        None_
        >>> map.insert("b", 2)
        None_
        >>> map.insert("c", 3)
        None_
        >>>
        >>> for key, val in map:
        ...     print("key:", key, "val:", val)
        ...
        key: a val: 1
        key: b val: 2
        key: c val: 3
        """
        return iter(self._dict.items())

    def iter_mut(self) -> t.Iterable[t.Tuple[K, Ref[V]]]:
        """An iterator visiting all key-value pairs in arbitrary order, with
        mutable references to the values. The iterator element type is
        ``Tuple[K, Ref[V]]``.

        >>> map = HashMap[str, int]()
        >>> map.insert("a", 1)
        None_
        >>> map.insert("b", 2)
        None_
        >>> map.insert("c", 3)
        None_
        >>>
        >>> for key, val in map.iter_mut():
        ...     val.modify(lambda v: v * 2)
        ...
        Ref(2)
        Ref(4)
        Ref(6)
        >>> for key, val in map:
        ...     print("key:", key, "val:", val)
        ...
        key: a val: 2
        key: b val: 4
        key: c val: 6
        """
        for key in self._dict:
            yield key, self._make_value_ref(key)

    def len(self) -> int:
        """Returns the number of elements in the map.

        Equivalent to ``len(map)``.

        >>> a = HashMap[int, str]()
        >>> a.len()
        0
        >>> a.insert(1, "a")
        None_
        >>> a.len()
        1
        """
        return len(self)

    def __len__(self):
        """Returns the number of elements in the map.

        >>> a = HashMap[int, str]()
        >>> len(a)
        0
        >>> a.insert(1, "a")
        None_
        >>> len(a)
        1
        """
        return len(self._dict)

    def is_empty(self) -> bool:
        """Returns :obj:`True` if the map contains no elements.

        >>> a = HashMap[int, str]()
        >>> a.is_empty()
        True
        >>> a.insert(1, "a")
        None_
        >>> a.is_empty()
        False
        """
        return not self._dict

    def drain(self) -> t.Iterable[t.Tuple[K, V]]:
        """Clears the map, returning all key-value pairs as an iterator.

        >>> from itertools import islice
        >>>
        >>> a = HashMap[int, str]()
        >>> a.insert(1, "a")
        None_
        >>> a.insert(2, "b")
        None_
        >>>
        >>> for k, v in islice(a.drain(), 1):
        ...     k == 1 or k == 2
        ...     v == "a" or v == "b"
        ...
        True
        True
        >>> a.is_empty()
        True
        """
        entries = list(self._dict.items())
        self._dict.clear()
        return entries

    def clear(self) -> None:
        """Clears the map, removing all key-value pairs.

        >>> a = HashMap[int, str]()
        >>> a.insert(1, "a")
        None_
        >>> a.clear()
        >>> a.is_empty()
        True
        """
        self._dict.clear()

    def entry(self, key: K) -> Entry[K, V]:
        """Gets the given key's corresponding entry in the map for in-place
        manipulation.

        >>> letters = HashMap[str, int]()
        >>>
        >>> for ch in "a short treatise on fungi":
        ...     counter = letters.entry(ch).or_insert(0)
        ...     _ = counter.modify(lambda i: i + 1)
        ...
        >>> letters["s"]
        2
        >>> letters["t"]
        3
        >>> letters["u"]
        1
        >>> letters.get("y")
        None_
        """
        if key in self:
            return OccupiedEntry(self, key)
        return VacantEntry(self, key)

    def get(self, key: K) -> Option[V]:
        """Returns a reference to the value corresponding to the keys.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> map.get(1)
        Some('a')
        >>> map.get(2)
        None_
        """
        val = self._dict.get(key, _nothing)  # type: ignore
        if val is _nothing:
            return None_()
        return Some(t.cast(V, val))

    def get_key_value(self, key: K) -> Option[t.Tuple[K, V]]:
        """Returns the key-value pair corresponding to the supplied key.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> map.get_key_value(1)
        Some((1, 'a'))
        >>> map.get_key_value(2)
        None_
        """
        return self.get(key).map(lambda v: (key, v))

    def __getitem__(self, key: K) -> V:
        """Returns a reference to the value corresponding to the supplied key.

        Raises :class:`KeyError` if the key is not present in the
        :class:`HashMap`.

        >>> map = HashMap[int, str]()
        >>> map[123] = "abc"
        >>> map[123]
        'abc'
        >>> map[234]
        Traceback (most recent call last):
            ...
        KeyError: 234
        """

        opt_val = self.get(key)
        if opt_val.is_none():
            raise KeyError(key)
        return opt_val.unwrap()

    def contains_key(self, key: K) -> bool:
        """Returns :obj:`True` if the map contains a value for the specified
        key.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> map.contains_key(1)
        True
        >>> map.contains_key(2)
        False
        """
        return key in self

    def __contains__(self, key: K) -> bool:
        """Returns :obj:`True` if the map contains a value for the specified
        key.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> 1 in map
        True
        >>> 2 in map
        False
        """
        return key in self._dict

    def get_mut(self, key: K) -> Option[Ref[V]]:
        """Returns a mutable reference to the value corresponding to the key.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> x = map.get_mut(1)
        >>> if x.is_some():
        ...     x.unwrap().set("b")
        ...
        >>> map[1]
        'b'
        """
        if key not in self._dict:
            return None_()

        def setter(val: V) -> None:
            self._dict[key] = val

        return Some(Ref(lambda: self._dict[key], setter))

    def insert(self, k: K, v: V) -> Option[V]:
        """Inserts a key-value pair into the map.

        If the map did not have this key present, :class:`None_` is returned.

        If the map did have this key present, the value is updated, and the old
        value is returned.

        >>> map = HashMap[int, str]()
        >>> map.insert(37, "a")
        None_
        >>> map.is_empty()
        False
        >>>
        >>> map.insert(37, "b")
        Some('a')
        >>> map.insert(37, "c")
        Some('b')
        >>> map[37]
        'c'
        """
        existing = self._dict.get(k, _nothing)  # type: ignore
        result: Option[V]
        if existing is _nothing:
            result = None_()
        else:
            result = Some(existing)
        self._dict[k] = v
        return result

    def __setitem__(self, key: K, value: V) -> None:
        """Inserts a key-value pair into the map.

        >>> map = HashMap[int, str]()
        >>> map[37] = "a"
        >>> map.is_empty()
        False
        >>>
        >>> map[37] = "b"
        >>> map[37] = "c"
        >>> map[37]
        'c'
        """

        self.insert(key, value)

    def remove(self, key: K) -> Option[V]:
        """Removes a key from the map, returning the value at the key if the key
        was previously in the map.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> map.remove(1)
        Some('a')
        >>> map.remove(1)
        None_
        """
        val = self._dict.pop(key, _nothing)  # type: ignore
        if val is _nothing:
            return None_()
        return Some(val)

    def remove_entry(self, key: K) -> Option[t.Tuple[K, V]]:
        """Removes a key from the map, returning the key and the value if the
        key was previously in the map.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> map.remove_entry(1)
        Some((1, 'a'))
        >>> map.remove(1)
        None_
        """
        return self.remove(key).map(lambda v: (key, v))

    def __delitem__(self, key: K) -> None:
        """Removes a key from the map.

        >>> map = HashMap[int, str]()
        >>> map.insert(1, "a")
        None_
        >>> map.is_empty()
        False
        >>> del map[1]
        >>> map.is_empty()
        True
        """
        self.remove(key)

    def retain(self, f: t.Callable[[K, Ref[V]], bool]) -> None:
        """Retains only the elements specified by the predicate.

        In other words, remove all pairs ``(k, v)`` such that ``f(k, Ref(v))``
        returns :obj:`False`.

        >>> map = HashMap.from_iter((x, x * 10) for x in range(8))
        >>> map.retain(lambda k, _v: k % 2 == 0)
        >>> len(map)
        4
        """
        for key in list(self._dict):
            if not f(key, self._make_value_ref(key)):
                del self._dict[key]

    def extend(self, it: t.Iterable[t.Tuple[K, V]]) -> None:
        """Extends a colluction with the contents of an iterator."""
        self._dict.update(it)

    def __eq__(self, other):
        """This method tests for ``self`` and ``other`` values to be equal, and
        is used by ``==``."""
        return self._dict == other

    def __repr__(self):
        return f"HashMap({self._dict!r})"

    @classmethod
    def from_iter(cls, it: t.Iterable[t.Tuple[K, V]]) -> "HashMap[K, V]":
        """Creates a value from an iterator."""
        hm = cls.new()
        hm.extend(it)
        return hm
