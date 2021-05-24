# patina

[![Documentation Status](https://readthedocs.org/projects/patina/badge/?version=latest)](https://patina.readthedocs.io/en/latest/?badge=latest)
![Supports Python 3.6 and up](https://img.shields.io/pypi/pyversions/patina)
[![PyPI](https://img.shields.io/pypi/v/patina)](https://pypi.org/project/patina/)

This is an implementation of Rust's Result and Option types in Python. Most
methods have been implemented, and the (very good) [original documentation] has
been adapted into docstrings.

The documentation for this package can be read [here][docs]. All doctests are
run and type-checked as part of the CI pipeline as unit tests. The tests are
direct ports of those in the Rust documentation.

[original documentation]: https://doc.rust-lang.org/std/result/
[docs]: https://patina.readthedocs.io/en/latest/

## Why?

2 reasons:
- Python (in 3.10) now has pattern matching, wouldn't it be cool if we could
  make the most of that?
- Sometimes it's nice to have types for your errors.
- Being able to `map` over possible failure can be very powerful.

Check this out:

```python
from patina import Some, None_

# This value is an Option[str]
maybe_value = api_call_that_might_produce_a_value()

match maybe_value.map(str.upper):  # Make it uppercase if it exists
    case Some(val):
        print("We got a val:", val)
    case None_():  # Don't forget the parentheses (otherwise it's binding a name)
        print("There was no val :(")
```

A similar thing can be done with the `Result` type (matching on `Ok` or `Err`).
This can be handy if you want to be more explicit about the fact that a function
might fail. If the function returns a `Result`, we can explicitly type the
possible error values.

If this all sounds good, I recommend looking into functional programming,
particularly of the ML variety (e.g. Haskell, OCaml, SML) or Rust.
