import sys
import termios
import tty


def getch(options=None):
    """getch function on linux"""

    # try:
    #     import termios
    # except ImportError:
    #     # Non-POSIX. Return msvcrt's (Windows') getch.
    #     import msvcrt  # pylint: disable=F0401
    #     return msvcrt.getch

    fdesc = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fdesc)
    try:
        tty.setraw(fdesc)
        char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fdesc, termios.TCSADRAIN, old_settings)
    if char == '\x03':
        raise KeyboardInterrupt
    elif char == '\x04':
        raise EOFError
    elif options is not None and char not in options:
        return getch(options)
    else:
        return char
