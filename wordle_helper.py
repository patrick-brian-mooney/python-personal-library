#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A helper for guessing Wordle entries based on already known information. It
prompts the user for already-known information and then prints a list of known
English words that match the specified info. It also requires a list of known
English words; I use one that I extracted directly from the Wordle JavaScript
code; previously I tested the script with a fuller list I got at
https://github.com/dwyl/english-words.

At the end of the run, it prints out a list of known English five-letter words,
based on the word list, that are not excluded by the information already known.
These words are ranked according to an algorithm that prioritizes:

  * words with more, rather than fewer, unique untried letters;
  * words containing letters that occur more frequently in the list of known
    five-letter words.

The overall strategy is not to try to guess right on the next guess, but to
use the next guess to elicit as much new information as possible while also
acting in a way that maximizes the likelihood of being right on the next guess,
to the extent that that doesn't conflict with getting as much new info as
possible.

Wordle is at https://www.powerlanguage.co.uk/wordle/.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
copyright 2022 by Patrick Mooney. It is free software, and you are welcome to
redistribute it under certain conditions, according to the GNU general public
license, either version 3 or (at your own option) any later version. See the
file LICENSE.md for details.
"""

import typing
import string
import sys

import pyximport; pyximport.install()

import wordle.wordle_utils as wu

print('\n\n\nStarting up ...')
print(f"    (running under Python {sys.version}")


def prompt_and_solve() -> typing.Tuple[str, str, typing.List[str]]:
    print(f"{len(wu.known_five_letter_words)} five-letter words known!\n\n")

    if input("Have you entirely eliminated any letters? ").strip().lower()[0] == 'y':
        elim = ''.join(set(wu.normalize_char_string(input("Enter all eliminated letters: "))))
    else:
        elim = ''

    if input("Do you have any letters yet without knowing their position? ").strip().lower()[0] == 'y':
        correct = wu.normalize_char_string(input("Enter all known letters: "))
    else:
        correct = ''

    if input("Have you finalized the position of any letters? ").strip().lower()[0] == 'y':
        possible = {}
        for i in range(1, 6):
            if input(f"Do you know the letter in position {i}? ").strip().lower()[0] == 'y':
                char = input(f"What is the letter in position {i}? ").strip().lower()
                assert len(char) == 1, "ERROR! You can only input one letter there!"
                possible[i] = char
            else:
                possible[i] = ''.join([c for c in string.ascii_lowercase if (c not in elim)])
    else:
        possible = {key: ''.join([c for c in string.ascii_lowercase if (c not in elim)]) for key in range(1, 6)}

    for c in correct:
        for i in range(1, 6):
            if len(possible[i]) == 1:  # Have we already determined for sure what letter is in a position?
                continue  # No need to ask if we've eliminated other characters, then.
            if input(f"Can you eliminate character {c} from position {i}? ").lower().strip() == "y":
                possible[i] = ''.join([char for char in possible[i] if char != c])

    known_letters = ''.join([s[0] for s in possible.values() if (len(s) == 1)])
    untried_letters = ''.join([c for c in string.ascii_lowercase if ((c not in elim) and (c not in known_letters))])

    letter_frequencies, possible_answers = wu.enumerate_solutions(possible, correct)
    return known_letters, untried_letters, letter_frequencies, possible_answers


if __name__ == "__main__":
    known_letters, untried_letters, letter_frequencies, possible_answers = prompt_and_solve()
    print("Possible answers:")

    if possible_answers:
        for w in wu.ranked_answers(possible_answers, letter_frequencies, untried_letters):
            print(w)
    else:
        print("No possibilities found!")
