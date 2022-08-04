#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cython: language_level=3
"""A module that supplies a class that can be used as a fake module that
supplies any number of fake decorators that do nothing. This is helpful as a
drop-in replacement for modules that may or may not be installed on the end-
user's system; it was originally written, for instance, to assist in helping
pure-Python code maintain pure-Python compatibility while still being able to
be sped up through Cython compilation. Any decorator requested from this
object-treated-as-a-module will do nothing.

So, for instance, you might use it like this:

    try:
        import cython
    except ImportError:
        from fake_decorator_module import fake_module as cython

and then you will be able to write

    @cython.cfunc
    def a_function(a, b):
        ...

... without worrying whether Cython is actually installed.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


from typing import Callable


def flexible_decorator(*args, **kwargs) -> Callable:
    """Functions either as a decorator that returns a function unchanged, or else as
    a factory that returns a decorator that returns a function changed.
    """
    if len(args) == 0:              # Only **kwargs passed? Must be that we're being invoked as a factory.
        return flexible_decorator   # Return ourselves to be invoked again with a different signature so we can pass back args[0]
    elif len(kwargs) == 0 and len(args) == 1 and callable(args[0]):
        return args[0]              # No keyword arguments, one positional argument, and it's callable? That's what we're being asked to decorate. Return it unchanged.
    else:                           # We're being called as a factory. Return ourselves to be invoked again as a decorator.
        return flexible_decorator


class StubDecoratorSupplier:
    """A class that serves as a drop-in replacement for "modules" that are supposed
    to supply decorators but that cannot be imported. It responds to a request for
    any (unknown) attribute by returning a stub decorator that simply returns the
    object it was passed.

    This is useful, for instance, for marking up code that can be run with Cython
    with decorators that provide useful information to the Cython compiler, but that
    will still run under pure Python without Cython installed: an instance of this
    class can be used in place of the Cython module if importing Cython raises an
    ImportError.

    Might fail if the attribute of the module that's trying to be located happens to
    be an attribute that this class inherits from OBJECT; these are all dunder names
    and most or all would be unusual to try to locate in a module. Still, if this
    starts happening, __getattr__ might need to be replaced with __getattribute__.
    """
    def __getattr__(self, *args, **kwargs):
        return flexible_decorator


fake_module = StubDecoratorSupplier()
