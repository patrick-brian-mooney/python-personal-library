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

import shelve

import pyximport; pyximport.install()


import wordle.wordle_utils as wu
import wordle.strategies as strategies


def exhaustively_analyze() -> None:
    for strat in strategies.Strategy.all_strategies():
        print(f'\nNow trying strategy {strat.__name__}')
        with shelve.open('solutions_cache', protocol=-1, writeback=True) as db:
            for solution in wu.known_five_letter_words:
                print(f"  Analyzing starting word success for solution {solution.upper()} ...")
                if strat.__name__ not in db:
                    db[strat.__name__] = dict()
                if solution not in db[strat.__name__]:
                    db[strat.__name__][solution] = strat.solve(solution)


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
