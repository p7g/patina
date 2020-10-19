.. result documentation master file, created by
   sphinx-quickstart on Sun Oct 18 00:00:38 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Patina - Rusty types for Python
===============================

This is an implementation of Rust's Result_ and Option_ types in Python. Almost
all methods have been implemented. Excluded are those that involve Rust's
borrowing semantics and implementations of traits, which are not trivially
supported in Python.

.. _Result: https://doc.rust-lang.org/std/result/enum.Result.html
.. _Option: https://doc.rust-lang.org/std/option/enum.Option.html

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   option
   result

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
