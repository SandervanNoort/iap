import os


def clear_screen():
    """Clear screen"""
    os.system("cls" if os.name == "nt" else "clear")
