#!/usr/bin/env python3
"""Routines for object examination."""


import pprint
import inspect
import pickle


def dump(obj):
    """Just dump a string representation of all object attributes

    Based on https://stackoverflow.com/a/192184/5562328
    """
    object_representation = {}.copy()
    for attr in dir(obj):
        object_representation[attr] = getattr(obj, attr)
    pprint.pprint(object_representation)

def unpickle_and_dump(the_file):
    """Like dump(), but unpickles the contents of a file, then dumps what comes out.
    """
    with open(the_file, 'rb') as f:
        data = pickle.load(f)
    dump(data)
    pprint.pprint(data)

def object_size_estimate(obj):
    pass

def class_methods_in_module(module_name, class_names=True, include_leading_underscores=False):
    """Get all class methods from a module."""
    ret = set()
    classes = inspect.getmembers(module_name, inspect.isclass)
    for c in classes:
        for m in c[1].__dict__:
            if not m.startswith('_') or include_leading_underscores:
                if class_names: ret |= set(["%s.%s" % (c[0], m)])
                else: ret.add(str(m))
    return ret


if __name__ == "__main__":
    import creatures
    pprint.pprint(class_methods_in_module(creatures, include_leading_underscores=True))
