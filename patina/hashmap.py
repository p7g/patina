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
    def __init__(self, table: "HashMap[K, V]", key: K):
        self._key = key
        self._table = table

    def or_insert(self, default: V) -> Ref[V]:
        return self.or_insert_with(lambda: default)

    @abstractmethod
    def or_insert_with(self, default: t.Callable[[], V]) -> Ref[V]:
        ...

    def or_insert_with_key(self, default: t.Callable[[K], V]) -> Ref[V]:
        return self.or_insert_with(partial(default, self._key))

    def key(self) -> K:
        return self._key

    @abstractmethod
    def and_modify(self, f: t.Callable[[Ref[V]], None]) -> "Entry[K, V]":
        ...


class OccupiedEntry(Entry[K, V]):
    __match_args__ = ("_key", "_val")

    def _make_value_ref(self) -> Ref[V]:
        return self._table._make_value_ref(self._key)

    def or_insert_with(self, default: t.Callable[[], V]) -> Ref[V]:
        return self._make_value_ref()

    def and_modify(self, f: t.Callable[[Ref[V]], None]) -> Entry[K, V]:
        f(self._make_value_ref())
        return self

    def remove_entry(self) -> t.Tuple[K, V]:
        return self._table.remove_entry(self._key).unwrap()

    def get(self) -> V:
        return self._table[self._key]

    _val = property(get)

    def get_mut(self) -> Ref[V]:
        return self._make_value_ref()

    def insert(self, value: V) -> V:
        return self._table.insert(self._key, value).unwrap()

    def remove(self) -> V:
        return self._table.remove(self._key).unwrap()

    def __repr__(self):
        return f"OccupiedEntry(key={self._key!r}, value={self.get()!r})"


class VacantEntry(Entry[K, V]):
    __match_args__ = ("_key",)

    def or_insert_with(self, default: t.Callable[[], V]) -> Ref[V]:
        self._table.insert(self._key, default())
        return self._table._make_value_ref(self._key)

    def insert(self, value: V) -> Ref[V]:
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
        self._dict = dct or {}

    @classmethod
    def new(cls):
        return cls()

    def keys(self) -> t.Iterable[K]:
        return self._dict.keys()

    def values(self) -> t.Iterable[V]:
        return self._dict.values()

    def _make_value_ref(self, key: K) -> Ref[V]:
        def set_value(val: V) -> None:
            self._dict[key] = val

        return Ref(lambda: self._dict[key], set_value)

    def values_mut(self) -> t.Iterable[Ref[V]]:
        for key in self._dict:
            yield self._make_value_ref(key)

    def iter(self) -> t.Iterable[t.Tuple[K, V]]:
        return iter(self)

    def __iter__(self):
        return self._dict.items()

    def iter_mut(self) -> t.Iterable[t.Tuple[K, Ref[V]]]:
        for key in self._dict:
            yield key, self._make_value_ref(key)

    def len(self) -> int:
        return len(self)

    def __len__(self):
        return len(self._dict)

    def is_empty(self) -> bool:
        return bool(self._dict)

    def drain(self) -> t.Iterable[t.Tuple[K, V]]:
        entries = list(self._dict.items())
        self._dict.clear()
        return entries

    def clear(self) -> None:
        self._dict.clear()

    def entry(self, key: K) -> Entry[K, V]:
        if key in self:
            return OccupiedEntry(self, key)
        return VacantEntry(self, key)

    def get(self, key: K) -> Option[V]:
        val = self._dict.get(key, _nothing)  # type: ignore
        if val is _nothing:
            return None_()
        return Some(t.cast(V, val))

    def get_key_value(self, key: K) -> Option[t.Tuple[K, V]]:
        return self.get(key).map(lambda v: (key, v))

    def __getitem__(self, key: K) -> V:
        return self.get(key).unwrap()

    def contains_key(self, key: K) -> bool:
        return key in self

    def __contains__(self, key: K) -> bool:
        return key in self._dict

    def get_mut(self, key: K) -> Option[Ref[V]]:
        # NOTE: not safe for concurrent access (no borrow checker)
        if key not in self._dict:
            return None_()

        def setter(val: V) -> None:
            self._dict[key] = val

        return Some(Ref(lambda: self._dict[key], setter))

    def insert(self, k: K, v: V) -> Option[V]:
        existing = self._dict.get(k, _nothing)  # type: ignore
        result: Option[V]
        if existing is _nothing:
            result = None_()
        else:
            result = Some(existing)
        self._dict[k] = v
        return result

    def remove(self, key: K) -> Option[V]:
        val = self._dict.pop(key, _nothing)  # type: ignore
        if val is _nothing:
            return None_()
        return Some(val)

    def remove_entry(self, key: K) -> Option[t.Tuple[K, V]]:
        return self.remove(key).map(lambda v: (key, v))

    def __delitem__(self, key: K) -> None:
        self.remove(key)

    def retain(self, f: t.Callable[[K, Ref[V]], None]) -> None:
        for key in self:
            if not f(key, self._make_value_ref(key)):
                del self._dict[key]

    def extend(self, it: t.Iterable[t.Tuple[K, V]]) -> None:
        self._dict.update(it)

    def __eq__(self, other):
        return self._dict == other

    def __repr__(self):
        return f"HashMap{self._dict!r}"

    @classmethod
    def from_iter(cls, it: t.Iterable[t.Tuple[K, V]]) -> "HashMap[K, V]":
        hm = cls.new()
        hm.extend(it)
        return hm
