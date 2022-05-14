#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility functions used by the other Wordle code.

Wordle is at https://www.powerlanguage.co.uk/wordle/.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
copyright 2022 by Patrick Mooney. It is free software, and you are welcome to
redistribute it under certain conditions, according to the GNU general public
license, either version 3 or (at your own option) any later version. See the
file LICENSE.md for details.
"""


import collections
import typing
import unicodedata

from pathlib import Path


# word_list_file = Path('/home/patrick/Documents/programming/resources/word-lists/dwyl/words_alpha.txt')
word_list_file = Path('/home/patrick/Documents/programming/resources/word-lists/wordle.list')


word_list_text = word_list_file.read_text()
known_english_words = [w.strip() for w in word_list_text.split('\n') if w.strip()]
known_five_letter_words = {w for w in known_english_words if len(w) == 5}


# A few variables we want to put in the global namespace now; we'll calculate real values later.
letter_frequencies = collections.Counter()
untried_letters = ''


# Some functions to help with normalization of text.
def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def normalize_char_string(s: str) -> str:
    return strip_accents(''.join([s for s in s.lower().strip() if s.isalpha()]))


def enumerate_solutions(possible: typing.Dict[int, str],
                        ambiguous_pos: str) -> typing.Tuple[collections.Counter, typing.Set[str]]:
    """Given POSSIBLE and AMBIGUOUS_POS, generate a list of words in the known words
    list that might be the word we're looking for, i.e. don't violate the currently
    known constraints.

    POSSIBLE is a dictionary mapping positions 1, 2, 3, 4, 5 to a string containing
    letters that might be in that position, AMBIGUOUS_POS is a string containing
    letters we know to be in the word but for which we haven't yet finalized the
    placement.

    Does not make any effor to rank the possible answers yet.

    Along the way, generates a Counter that maps letters in the words that might be
    the answer we're looking for to how often those letters occur in the possibility
    set.

    REturns a Set of maybe-words and the Counter mapping the letters in those words
    to their frequency in the maybe-words.

    #FIXME: there's a good chance this would be faster if we used regex-based
    matching instead of nested loops.
    """
    possible_answers = set()

    num_found = 0
    for c1 in possible[1]:
        for c2 in possible[2]:
            for c3 in possible[3]:
                for c4 in possible[4]:
                    for c5 in possible[5]:
                        word = c1 + c2 + c3 + c4 + c5
                        if word not in known_five_letter_words:
                            continue
                        if (len(ambiguous_pos) > 0) and (ambiguous_pos[0] not in word):
                            continue
                        if (len(ambiguous_pos) > 1) and (ambiguous_pos[1] not in word):
                            continue
                        if (len(ambiguous_pos) > 2) and (ambiguous_pos[2] not in word):
                            continue
                        if (len(ambiguous_pos) > 3) and (ambiguous_pos[3] not in word):
                            continue
                        if (len(ambiguous_pos) > 4) and (ambiguous_pos[4] not in word):
                            continue

                        num_found += 1
                        possible_answers.add(word)

    letter_frequencies = collections.Counter(''.join(possible_answers))
    return letter_frequencies, possible_answers


def untried_word_score(w: str) -> int:
    """Produce a score for W, a word that has not yet been attempted. The score depends
    on how often each letter in W that hasn't yet been tried appears in the sample
    of five-letter words. This count is pre-computed and stored in the
    LETTER_FREQUENCIES variable. Letters that have already been tried and are known
    to occur in the word we're trying to guess contribute nothing to the calculated
    score: the score is designed to favor getting more information from the next
    guess, not to increase the likelihood of making the next guess the correct one.
    (We're trying to minimize the overall number of guesses, not to win on the next
    guess.) Repeated letters, after the first occurrence, also do not count toward
    the word's overall score: they don't elicit new information, either. "As many
    new letters as possible" is further incentivized by multiplying the derived
    score-sum by the number of unique letters in the word to derive the final score.
    """
    global letter_frequencies, untried_letters
    return sum([letter_frequencies[c] for i, c in enumerate(w) if ((c in untried_letters) and (c not in w[:i]))]) * len(set(w))


def ranked_answers(possible_answers: typing.List[str]):

    return sorted(possible_answers, key=untried_word_score, reverse=True)
