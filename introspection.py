#!/usr/bin/env python3
"""Routines for object examination."""

def dump(obj):
    """Just dump a string representation of all object attributes
    
    Based on https://stackoverflow.com/a/192184/5562328
    """
    for attr in dir(obj):
        return("obj.%s = %s" % (attr, getattr(obj, attr)))

def object_size_estimate(obj):
    pass

if __name__ == "__main__":
    pass
