#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#cython: language_level=3

"""Collection of Strategy classes used by the Wordle-analyzing code.

Wordle is at https://www.powerlanguage.co.uk/wordle/.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
copyright 2022 by Patrick Mooney. It is free software, and you are welcome to
redistribute it under certain conditions, according to the GNU general public
license, either version 3 or (at your own option) any later version. See the
file LICENSE.md for details.
"""

import collections
import string
import typing

import wordle.wordle_utils as wu


class Strategy:
    """An abstract strategy, specifying what parameters are necessary. All
    Strategies MUST be subclasses of this class.

    Strategies are "degenerate" classes -- mere packages of functions. They need not
    even be instantiated to do their work: none of their methods takes a SELF
    parameter! (All their methods are static or class methods.) They are mini-
    modules that keep their related functions in packages, nothing else. All that
    instantiating them achieves is checking that all of a Strategy's abstract
    methods have been filled in.
    """
    @classmethod
    def all_strategies(cls) -> typing.Generator[type, None, None]:
        """Returns a list of all known strategies.
        """
        for t in cls.__subclasses__():
            yield t
            yield from t.all_strategies()           #FIXME! Check to see whether this works?

    @staticmethod
    def rank(possible_words: typing.List[str]) -> typing.List[str]:
        """Given POSSIBLE_WORDS, rank them so that (what the strategy thinks is the)
        most-likely word comes first, followed by the next-most-likely, etc.
        """

    @staticmethod
    # @abc.abstractmethod
    def score(letter_frequencies: collections.Counter,
              untried_letters: str,
              w: str) -> int:
        """Assign a score to an individual guess. A guess that the Strategy thinks is
        "better" should get a higher score. Strategies need not worry about how their
        rankings compare to the rankings of other Strategies; that comparison is never
        made.
        """

    @classmethod
    # @abc.abstractmethod
    def solve_from(cls, answer: str,
                   start_from: str) -> typing.Dict:
        """Implements the actual strategy for the class: Given START_FROM, a starting
        guess, analyze how long it takes, implementing the strategy, to get to ANSWER.
        """

    @classmethod
    def solve(cls, answer: str) -> typing.Dict:          #FIXME! More specific return type.
        """Given ANSWER, the answer to the Wordle in question, try to derive that answer by
        starting from each possible starting word and applying the particular strategy,
        tracking how successful it is in each instance, and returning a dictionary that
        both summarizes the overall performance of the strategy and includes
        move-by-move details about how each starting word played out.
        """
        ret = {w: cls.solve_from(answer, w) for w in wu.known_five_letter_words}
        # FIXME: summary analysis!
        return ret

    @classmethod
    def solve_from(cls, answer: str,
                   start_from: str) -> typing.Tuple[typing.Dict[str, typing.Union[str, dict, bool]]]:
        """Given ANSWER, the answer to the Wordle, derive it from START_FROM using the
        current Strategy, tracking moves made and how that changes the parameters of
        what answers are remaining.
        """
        possibilities = {i: set(string.ascii_lowercase) for i in range(1, 6)}
        ret, done = list(), False
        guess, unknown_pos = start_from, ''

        while not done:
            turn_data = {
                'move': guess,
                'initial possible letters': {key: sorted(list(value)) for key, value in possibilities.items()},
                'known letters with unknown position before guess': unknown_pos,
            }
            ret.append(turn_data)
            done, unknown_pos, possibilities = wu.evaluate_guess(guess, answer, possibilities, unknown_pos)
            untried_letters = ''.join([c for c in string.ascii_lowercase if c not in ''.join(i['move'] for i in ret)])
            letter_frequencies, remaining_possibilities = wu.enumerate_solutions(possibilities, unknown_pos)
            possible_answers = {sol: cls.score(letter_frequencies, untried_letters, sol) for sol in remaining_possibilities}
            possible_answers = dict(sorted(possible_answers.items(), key=lambda kv: kv[1], reverse=True))
            turn_data.update({
                'possible letters after guess': {key: sorted(list(value)) for key, value in possibilities.items()},
                'known letters with unknown position after guess': unknown_pos,
                'remaining possibilities': possible_answers,
                'exhausted erroneously': any([not len(v) for v in possibilities.values()]),
                'solved': done,
            })
            if len(ret) > 5:
                done = True
            elif not done:
                guess = list(possible_answers.keys())[0]
        return tuple(ret)


class GetMaximumInfoHardMode(Strategy):
    @staticmethod
    def score(letter_frequencies: collections.Counter,
              untried_letters: str,
              w: str) -> int:
        return wu.untried_word_score(letter_frequencies, untried_letters, w)


class GetMaximumInfoEasyMode(Strategy):
    pass

