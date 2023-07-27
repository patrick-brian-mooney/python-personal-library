#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A routine to ask the user to make a choice from a predetermined set of choices.

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import collections
import typing

import text_handling        # https://github.com/patrick-brian-mooney/python-personal-library/
import patrick_logger       # same


def menu_choice(choice_menu: typing.Hashable,
                prompt: str) -> str:
    """Takes a menu description, passed in as CHOICE_MENU (see below for format),
     and asks the user to make a choice between the options. It then passes back
     the user's choice to the caller.

    CHOICE_MENU is an OrderedDict (or similar, including regular dicts in Python
    3.7+) mapping a list of options to be typed (short strings, each of which is
    ideally a single letter) to a full description of what that option means (a
    longer string). For example:

        OrderedDict([
                     ('a', 'always capitalize'),
                     ('y', 'yes'),
                     ('n', 'never')
                    ])

    As a special case, if both parts of an entry in the OrderedDict are two hyphens,
    that entry is not a valid menu choice; it is printed as-is, as a visual
    separator, but is not a selectable option.

    PROMPT is a direct request for input; printed after all the menu options have
    been displayed.

    Returns a string, the response the user typed that was validated as an allowed
    choice.
    """
    max_menu_item_width = max(len(x) for x in choice_menu)
    menu_column_width = max_menu_item_width + len("  [ ") + len(" ]")
    spacing_column_width = 3
    options_column_width = text_handling.terminal_width() - (menu_column_width + spacing_column_width + 1)

    # OK, let's print this menu.
    print()
    for option, text in choice_menu.items():
        if (option == '--') and (text == '--'):
            current_line = '  --  ' + ' ' * (max_menu_item_width - len('--')) + ' ' * spacing_column_width + '-----'
        else:
            current_line = '[ %s ]%s%s' % (option, ' ' * (max_menu_item_width - len(option)), ' ' * spacing_column_width)
            text_lines = text_handling._get_wrapped_lines(text, enclosing_width=options_column_width)
            if len(text_lines) == 1:
                current_line = current_line + text_lines[0]
            else:
                current_line = current_line + text_lines.pop(0)     # Finish the line with the first line of the description
                left_padding = '\n' + (' ' * (menu_column_width + spacing_column_width))
                current_line = current_line + left_padding + left_padding.join(text_lines)     # Add in the rest of the lines
        print(current_line)
    print()
    patrick_logger.log_it("INFO: multi_choice_menu.py: menu laid out in %d lines." % len(current_line.split('\n')), 2)
    patrick_logger.log_it("INFO: multi_choice_menu.py: menu contents are: %s" % current_line, 4)

    # Now, get the user's choice
    choice = 'not a legal option'
    legal_options = [ k.casefold() for k, v in choice_menu.items() if ((k != '--') or (v != '--')) ]
    patrick_logger.log_it("INFO: multi_choice_menu.py: Legal options for this menu are %s" % legal_options, 2)
    tried_yet = False
    while choice.casefold() not in legal_options:
        if tried_yet:           # If the user has got it wrong at least once...
            prompt = prompt.strip() + " [ %s ] " % ('/'.join(legal_options))
        choice = input(prompt.strip() + " ").strip()
        tried_yet = True
    return choice


def easy_menu_choice(choice_menu: typing.Iterable[str],
                     prompt: str) -> str:
    """Does the same thing as menu_choice(), except that it takes an iterable of
    strings instead of a dictionary mapping responses to strings. It then auto-
    calculates responses itself and passes the manufactured response -> prompts dict
    to menu_choice().

    Does not return the short response the user typed, as menu_choice() does,
    because the auto-0calculated menu choice is not meaningful to the calling code.
    Instead, returns the full prompt string.
    """
    assert isinstance(choice_menu, collections.Iterable)
    assert all([isinstance(i, str) for i in choice_menu])
    assert isinstance(prompt, str)

    menu = collections.OrderedDict()

    def unused_answer(option: str) -> str:
        used_keys = set([i.strip().casefold() for i in menu.keys()])
        for length in range(1, 1+len(option)):
            for i in range(len(option) - length):
                if option[i: i+length].strip().casefold() not in used_keys:
                    return option[i: i+length]

        raise RuntimeError("Cannot derive a response key for option %s!!!" % option)

    for item in choice_menu:
        menu[unused_answer(item)] = item

    ans = menu_choice(menu, prompt)

    # This next bit is to make absolutely sure we allow for differences in case and with leading/trailing space
    return {k.strip().casefold(): v for k, v in menu.items()}[ans.strip().casefold()]
    # FIXME: The above line may process incorrectly if multiple keys that differ only in case are in the dict!


if __name__ == "__main__":
    patrick_logger.verbosity_level = 3
    print("INFO: Terminal width is %d.\n" % text_handling.terminal_width())
    response = "N"
    the_menu = collections.OrderedDict([
        ('Y', 'Yes, I do'),
        ('N', 'No, not yet')
    ])
    while response.lower() == "n":
        response = menu_choice(the_menu, "You do understand that this is not a program itself, but rather a utility "
                                         "for other programs to use, don't you?")
        print("\nYou chose '%s'." % response)
