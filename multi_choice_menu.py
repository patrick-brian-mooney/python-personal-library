#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A routine to ask the user to make a choice from a predetermined set of choices.
"""


from collections import OrderedDict

import text_handling, patrick_logger    # https://github.com/patrick-brian-mooney/python-personal-library/


def menu_choice(choice_menu, prompt):
    """Takes a menu description, passed in as CHOICE_MENU (see below for format),
     and asks the user to make a choice between the options. It then passes back
     the user's choice to the caller.

    :param choice_menu: an OrderedDict that maps a list of options to be typed
                        (short strings, each of which is ideally a single
                        letter) to a full description of what that option means
                        (a longer string). For example:

                        OrderedDict([
                                     ('a', 'always capitalize'),
                                     ('y', 'yes'),
                                     ('n', 'never')
                                    ])
    :param prompt:      a direct request for input; printed after all of the
                        menu options have been displayed.
    :return:            a string: the response the user typed that was
                        validated as an allowed choice.
    """
    max_menu_item_width = max(len(x) for x in choice_menu)
    menu_column_width = max_menu_item_width + len("  [ ") + len(" ]")
    spacing_column_width = 3
    options_column_width = text_handling.terminal_width() - (menu_column_width + spacing_column_width + 1)

    # OK, let's print this menu.
    print()
    for option, text in choice_menu.items():
        current_line = '[ %s ]%s%s' % (option, ' ' * (max_menu_item_width - len(option)), ' ' * spacing_column_width)
        text_lines = text_handling._get_wrapped_lines(text, enclosing_width=options_column_width)
        if len(text_lines) == 1:
            current_line = current_line + text_lines[0]
        else:
            current_line = current_line + text_lines.pop(0)     # Finish the line with the first line of the description
            left_padding = '\n' + (' ' * (menu_column_width + spacing_column_width))
            current_line = current_line + left_padding.join(text_lines)     # Add in the rest of the description lines
        print(current_line)
    print()
    patrick_logger.log_it("INFO: multi_choice_menu.py: menu laid out in %d lines." % len(current_line.split('\n')), 2)
    patrick_logger.log_it("INFO: multi_choice_menu.py: menu contents are: %s" % current_line, 4)

    # Now, get the user's choice
    choice = 'not a legal option'
    legal_options = [ l.lower() for l in choice_menu ]
    patrick_logger.log_it("INFO: multi_choice_menu.py: Legal options for this menu are %s" % legal_options, 2)
    tried_yet = False
    while choice.lower() not in legal_options:
        if tried_yet:           # If the user has got it wrong at least once.
            prompt = prompt.strip() + " [ %s ] " % ('/'.join(choice_menu))
        choice = input(prompt.strip() + " ").strip()
        tried_yet = True
    return choice


if __name__ == "__main__":
    patrick_logger.verbosity_level = 3
    print("INFO: Terminal width is %d.\n" % text_handling.terminal_width())
    response = "N"
    the_menu = OrderedDict([
                            ('Y', 'Yes, I do'),
                            ('N', 'No, not yet')
                            ])
    while response.lower() == "n":
        response = menu_choice(the_menu, "You do understand that this is not a program itself, but rather a utility for other programs to use, don't you?")
        print("\nYou chose '%s'." % response)
