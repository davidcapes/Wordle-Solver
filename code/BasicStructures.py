import numpy as np
from enum import Enum


# Global constants / Macros.
ROWS = 6
COLUMNS = 5

NULL_CHAR = '*'


# Color class.
class Color(Enum):
    GREY = 0
    YELLOW = 1
    GREEN = 2

    def next_color(self):
        return Color((self.value + 1) % len(Color))

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return self.value

    def __lt__(self, other):
        return self.value < other.value


# Cell class.
class Square:

    def __init__(self, color=Color.GREY, char=NULL_CHAR):
        self.color = color
        self.char = char

    def __str__(self):
        return str(self.color) + str(self.char)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.color) + len(Color)*hash(self.char)


# Constraints class.
class Constraints:

    def __init__(self):
        self.grid = np.array([[Square() for _ in range(COLUMNS)] for _ in range(ROWS)])

    def __str__(self):
        hashable = []
        for r in range(ROWS):
            for c in range(COLUMNS):
                if self.grid[r][c].char != NULL_CHAR:
                    color = self.grid[r][c].color
                    char = self.grid[r][c].char
                    hashable.append((color, char))
        hashable.sort()
        return str(tuple(hashable))

    def get_first_blank(self):
        for r in range(ROWS):
            for c in range(COLUMNS):
                if self.grid[r][c].char == NULL_CHAR:
                    return r, c
        return None

    def get_last_char(self):
        for r in range(ROWS - 1, 0 - 1, -1):
            for c in range(COLUMNS - 1, 0 - 1, -1):
                if self.grid[r][c].char != NULL_CHAR:
                    return r, c
        return None
