#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sequentially tries all possible Wordle words as starting guesses relative to
each possible "correct answer," then plays out the remainder of the round using
a variety of strategies, tracking how each starting word/strategy combination
performs across the whole problem set. Since each strategy needs to evaluate
each starting word relative to each answer, the strategies each need to try
5,331,481 (2309 * 2309 -- there are 2309 Wordle words) combinations.

Wordle is at https://www.powerlanguage.co.uk/wordle/.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
copyright 2022 by Patrick Mooney. It is free software, and you are welcome to
redistribute it under certain conditions, according to the GNU general public
license, either version 3 or (at your own option) any later version. See the
file LICENSE.md for details.
"""


import time
import shelve

import pyximport; pyximport.install()


import wordle.wordle_utils as wu
import wordle.strategies as strategies


def exhaustively_analyze_very_slow() -> None:
    """For each strategy, evaluate each word that could possibly be an answer by
    starting from each possible starting word and using the strategy to solve from
    that starting word, keeping notes on moves made and how the parameters shift
    along the way.

    This is a rather slow version because dereferencing dictionaries multiple times
    inside a shelve-backed hashable is necessarily slow. Use the faster, similarly
    named exhaustively_analyze() function below, instead.

    This gets slower as the analysis of a specific strategy progresses.
    """
    for strat in strategies.Strategy.all_strategies():
        print(f'\nNow trying strategy {strat.__name__}')
        for i, solution in enumerate(wu.known_five_letter_words, 1):
            print(f"  Analyzing starting word success for solution #{i}: {solution.upper()} ...")
            with shelve.open('solutions_cache', protocol=-1, writeback=True) as db:
                if strat.__name__ not in db:
                    db[strat.__name__] = dict()
                t_start = time.monotonic()
                if solution not in db[strat.__name__]:
                    db[strat.__name__][solution] = strat.solve(solution)
                    t_done = time.monotonic()
                    print(f"    ... analyzed in {t_done - t_start} seconds!")
            try:
                t_update, _ = time.monotonic(), t_done
            except (NameError,):
                pass
            else:
                print(f"    ... database update took {t_update - t_done} seconds!")
                del t_done, t_update


def exhaustively_analyze() -> None:
    """Does the same thing as exhaustively_analyze_very_slow(), above, but is much
    faster.
    """
    def key_name(strategy: str, answer: str) -> str:
        return str((strategy, answer))

    for strat in strategies.Strategy.all_strategies():
        print(f"\nNow trying strategy {strat.__name__}")
        for i, solution in enumerate(sorted(wu.known_five_letter_words), 1):
            print(f"  Analyzing starting word success for solution #{i}: {solution.upper()} ...")
            t_open = time.monotonic()
            with shelve.open('solutions_cache', protocol=-1, writeback=True) as db:
                t_start = time.monotonic()
                print(f"    ... initializing database connection took {t_start - t_open} seconds!")
                key = key_name(strat.__name__, solution)
                if key not in db:
                    analysis, t_done = strat.solve(solution), time.monotonic()
                    print(f"    ... analyzed in {t_done - t_start} seconds!")
                    db[key], t_stash = analysis, time.monotonic()
                    print(f"    ... analysis stashed in database in {t_stash - t_done} seconds!")
            try:
                t_update, _ = time.monotonic(), t_stash
            except (NameError, ):
                pass
            else:
                print(f"    ... database update took {t_update - t_stash} seconds!")
                del t_stash, t_done, t_update


if __name__ == "__main__":
    if False:                        # test harness; in this case, for timing
        import sys

        data = strategies.GetMaximumInfoHardMode.solve('ninja')
        dump_path = Path('output.json').resolve()
        print(f"Dumping JSON data to {dump_path} ...")
        with open(dump_path, 'wt') as json_file:
            json.dump(data, json_file, ensure_ascii=False, default=str, indent=2)
        print("Finished!\n\n")

        sys.exit()


    print("Starting up ...")
    exhaustively_analyze()
