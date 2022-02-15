#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A helper for guessing Wordle entries based on already known information. It
prompts the user for already-known information and then prints a list of known
English words that match the specified info. It also requires a list of known
English words; I use one from https://github.com/dwyl/english-words.

Wordle is at https://www.powerlanguage.co.uk/wordle/.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
copyright 2022 by Patrick Mooney. It is free software, and you are welcome to
redistribute it under certain conditions, according to the GNU general public
license, either version 3 or (at your own option) any later version. See the
file LICENSE.md for details.
"""


from pathlib import Path
import string
import unicodedata


word_list_file = Path('/home/patrick/Documents/programming/resources/word-lists/dwyl/words_alpha.txt')


def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def normalize_char_string(s: str) -> str:
    return strip_accents(''.join([s for s in s.lower().strip() if s.isalpha()]))


word_list_text = word_list_file.read_text()
known_english_words = [w.strip() for w in word_list_text.split('\n') if w.strip()]
known_five_letter_words = {w for w in known_english_words if len(w) == 5}

possible = {}

if input("Have you entirely eliminated any letters? ").strip().lower()[0] == 'y':
    elim = normalize_char_string(input("Enter all eliminated letters: "))
else:
    elim = ''

if input("Do you have any letters yet without knowing their position? ").strip().lower()[0]:
    correct = normalize_char_string(input("Enter all known letters: "))
else:
    correct = ''

for i in range(1, 6):
    if input(f"Do you know the letter in position {i}? ").strip().lower()[0] == 'y':
        char = input(f"What is the letter in position {i}? ").strip().lower()
        assert len(char) == 1, "ERROR! You can only input one letter there!"
        possible[i] = char
    else:
        possible[i] = ''.join([c for c in string.ascii_lowercase if (c not in elim)])

for c in correct:
    for i in range(1, 6):
        if input(f"Can you eliminate character {c} from position {i}? ").lower().strip() == "y":
            possible[i] = ''.join([char for char in possible[i] if char != c])

print("Possible answers:")

num_found = 0
for c1 in possible[1]:
    for c2 in possible[2]:
        for c3 in possible[3]:
            for c4 in possible[4]:
                for c5 in possible[5]:
                    word = c1 + c2 + c3 + c4 + c5
                    if word not in known_five_letter_words:
                        continue
                    if (len(correct) > 0) and (correct[0] not in word):
                        continue
                    if (len(correct) > 1) and (correct[1] not in word):
                        continue
                    if (len(correct) > 2) and (correct[2] not in word):
                        continue
                    if (len(correct) > 3) and (correct[3] not in word):
                        continue
                    if (len(correct) > 4) and (correct[4] not in word):
                        continue

                    num_found += 1
                    print(word)

if not num_found:
    print("No possibilities found!")
