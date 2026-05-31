#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module contains a set of GUI tools for redirecting text output streams
to GUI widgets created with Tkinter. They assume they are running in an
application that is already structured around a Tkinter event loop.

The first redirects streams to a text box. It is partly based on Mark Lutz,
*Programming Python*, pp. 624-25. Following it are a convenience function for
invocation and a convenience decorator for class methods.

These functions cause GUI updates directly and are therefore not safe to use
from threads other than the main Tkinter thread!

This code is copyright 2024 by Patrick Mooney. It is licensed under the GPL,
either version 3 or (at your option) under any later version. See the file
LICENSE.md for details.
"""


import sys
import tkinter as tk
import tkinter.scrolledtext

from typing import Any, Callable, List, Optional


class TextBoxStreamRedirector(object):
    """Wraps a Tkinter ScrolledText object to manage output from a function printing to
    stdout/stderr.
    """
    font = ('courier', 9, 'normal')              # in class for all, self for one

    def __init__(self, parent = None,
                 window_title: Optional[str] = None):
        self.parent = parent or tk.Toplevel()
        self.text = tk.scrolledtext.ScrolledText(self.parent)
        self.text.config(font=self.font)
        self.text.pack()
        if not parent:
            self.window_title = window_title

    def write(self, text: str):
        self.text.insert(tk.END, str(text))
        self.text.see(tk.END)
        self.text.update()                       # update gui after each line

    def writelines(self, lines: List[str]):                 # lines already have '\n'
        for line in lines:
            self.write(line)


def redirect_prints_to_text_box(func: Callable,
                                *pargs,
                                tk_parent = None,
                                window_title: Optional[str] = 'output',
                                stream_redirector_class: Callable = TextBoxStreamRedirector,
                                **kwargs) -> Any:
    """Call a function, re-routing stdout and stderr to a TextBoxStreamRedirector
    object (or, if specified, another, similar object). Note that, unlike in Lutz's
	example code, and perhaps counter-intuitively, stdin is ot rerouted here.
    """
    save_streams = sys.stdout, sys.stderr
    try:
        sys.stdout = stream_redirector_class(window_title=window_title, parent=tk_parent)
        sys.stderr = sys.stdout
        return func(*pargs, **kwargs)
    finally:
        sys.stdout, sys.stderr = save_streams


def textbox_redirector(window_title: Optional[str] = 'output',
                       tk_parent: Optional = None) -> Callable:
    """Wraps the function redirect_prints_to_text_box in a decorator so it can easily
    be used to wrap functions and methods and director their text output to a pop-up
    window.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return redirect_prints_to_text_box(func, *args, window_title=window_title,
                                               tk_parent=tk_parent, **kwargs)
        return wrapper
    return decorator


def fake_tk_for_text_box(func: Callable,
						 *pargs,
                         window_title: Optional[str] = 'output',
                         stream_redirector_class: Callable = TextBoxStreamRedirector,
                         **kwargs) -> Any:
    """Convenience function: Make it possible to run a non-Tkinter-based
    functions by creating a fake Tkinter main window, withdrawing it, and
    calling redirect_prints_to_text_box to call a specified function with
    specified parameters. Once the function returns
    """
    root = tk.Tk()
    root.title(window_title)

    redirect_prints_to_text_box(func,*pargs, tk_parent=root,
                                stream_redirector_class=stream_redirector_class, **kwargs)

    root.mainloop()


if __name__ == "__main__":
    pass
