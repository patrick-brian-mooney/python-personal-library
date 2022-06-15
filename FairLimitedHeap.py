#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A set of classes that implement fair limited heaps, a set of softly-limited-
size heaps that are "fair" in the sense that they will break their soft size
limit rather than ejecting low-scoring members with a score that's held by
other items still in the heap. Heaps will grow in size until all of the low-
scoring members can be ejected together.
"""


import collections
import heapq
import numbers
import reprlib
import typing


class FairLimitedHeap(collections.abc.Iterable):
    """A heap implemented using the heapq module that has a limited size. The size
    limit is a "soft" or "fair" limit: it tries to keep SOFT_LIMIT items (if at
    least that many items have been added to the heap in the first place), but will
    keep more if the worst-scored items all score equally poorly. So, for instance,
    pushing a single new item onto a heap that has exactly SOFT_LIMIT items will not
    delete a single item from the bottom of the heap if multiple items at the bottom
    of the heap all have the same low score.

    For instance, if there is a heap of 100 items, and the soft limit is 100, and
    the four lowest-ranked items all have the same low score, then:

    * Pushing an item scoring above that low score will increase the size of the
      heap to 101, because none of the items with the low score has a score any
      lower than any of the others, so none of them is removed; and
    * pushing another item scoring above that low score will increase the size of
      the heap to 102, for that same reason; same with pushing another item with a
      score above that low score, which will increase the heap size to 103; and
    * pushing a fourth item above that low score will add the item to the heap,
      temporarily increasing the size of the heap to 104 before removing all four of
      the equally low-scoring items and taking the heap size down to 100.

    The score of items must be manually specified when adding an item to the heap.
    Items added to the heap must be orderable for this to work. Internally, the heap
    is a list of (score, item) tuples, and rely on Python's short-circuiting of
    tuple comparisons to keep the heap sorted. (The fact that items with identical
    scores will be ordered based on the ordering of the items being stored both
    implies that the heap does not preserve insertion order for same-scored items
    and is the reason why items scored must be orderable.)
    """
    def __init__(self, soft_limit: int = 100,
                 initial: typing.Iterable = ()) -> None:
        """If INITIAL is specified, it must be an iterable of (value, item) tuples.
        """
        if initial:
            for item, _ in initial:
                assert isinstance(item, numbers.Number)
        self._soft_limit = soft_limit
        self._data = [][:]
        for item, value in initial:
            self.push(value, item)

    def __str__(self) -> str:
        return f"< {self.__class__.__name__} object, with {len(self._data)} items having priorities from {self._data[0][0]} to {self._data[-1][0]} >"

    def __repr__(self) -> str:
        """Limit how many items are displayed in the __repr__ by using reprlib.
        """
        return f"{self.__class__.__name__} ({reprlib.repr(self._data)})"

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        return self._data == other._data

    def __bool__(self) -> bool:
        return bool(self._data)

    def __iter__(self) -> typing.Iterator:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, item) -> typing.Any:
        return self._data[item][1]               # return only the item's VALUE, not its SCORE.

    def __setitem__(self, key, newvalue):
        raise TypeError(f"Cannot directly set individual items in a {self.__class__.__name__}! Use .push() to add a value to the heap instead.")

    def push(self, item: typing.Any,
              value: numbers.Number) -> None:
        heapq.heappush(self._data, (value, item))
        if len(self._data) <= self._soft_limit:
            return

        # Find the index of the item after last item in the heap with same VALUE as the item at the low end of the heap
        for index, item in enumerate(self._data):
            if index == 0:
                comp_value = item[0]
            elif item[0] != comp_value:     # exact equality good enough, even if difference is tiny.
                break

        if (len(self._data) - index) >= self._soft_limit:
             for i in range(index):
                 heapq.heappop(self._data)

    def pop(self, also_return_score: bool = False) -> typing.Any:
        if also_return_score:
            return heapq.heappop(self._data)
        else:
            return heapq.heappop(self._data[1])

    def as_sorted_list(self, include_values: bool = False) -> typing.List[typing.Tuple[numbers.Number, typing.Any]]:
        """Returns the contents of the heap in sorted-by-priority order. If
        INCLUDE_VALUES is True (not the default), returns a set of (value, item)
        tuples instead of just the items.
        """
        if include_values:
            return sorted(self._data)
        else:
            return [i[1] for i in sorted(self._data)]


class NonNanFairLimitedHeap(FairLimitedHeap):
    """Just Like FairLimitedHeap, except that it silently declines to push items
    onto the heap if the vlue assoociated with the item is a NaN value.
    """
    def push(self, item: typing.Any,
             value: numbers.Number) -> None:
        import numpy as np      # No need to make the entire project dependent on numpy if this class isn't used.
        if np.isnan(value):
            return
        else:
            FairLimitedHeap.push(self, item, value)
