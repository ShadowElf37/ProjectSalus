class Ansi:
    ESC = "\x1b"
    def __init__(self, codes):
        self.codes = tuple(str(c) for c in codes)
    def __str__(self):
        return "\x1b[{}m".format(";".join(self.codes))
    def __mul__(self, other):
        return Ansi(self.codes + other.codes)
    __rmul__ = __mul__
    def __add__(self, other):
        if isinstance(other, str):
            return str(self) + other
        raise ValueError
    def __radd__(self, other):
        if isinstance(other, str):
            return other + str(self)
        raise ValueError

def HTRGB(hex):
    hex = hex.strip('#')
    l = len(hex)
    scalar = 6//l
    if scalar == 0:
        raise ArithmeticError('Can\'t solve > 24-bit RGB values')
    elif scalar == 6:
        return (int(hex*2, 16),)*3
    return int(hex[:l//3]*scalar, 16), int(hex[l//3:2*l//3]*scalar, 16), int(hex[2*l//3:]*scalar, 16)

def FG(r, g, b):
    return Ansi((38, 2, r, g, b))
def BG(r, g, b):
    return Ansi((48, 2, r, g, b))

def _fb(r, g, b):
    return FG(r, g, b), BG(r, g, b)


PURPLE, BG_PURPLE = _fb(0xaa, 0x00, 0xff)
PURPLE_DARK, BG_PURPLE_DARK = _fb(0x55, 0x00, 0xaa)
INDIGO, BG_INDIGO = _fb(0x77, 0x00, 0xff)

defns = {
    "NORMAL": 0,
    "RESET": 0,
    "BOLD": 1,
    "FAINT": 2,
    "ITALIC": 3,
    "UNDERLINE": 4,
    "BLINK": 5,
    "BLINK_FAST": 6,
    "INVERT": 7,
    "STRIKETHROUGH": 9,
    "FRAKTUR": 20,

    "BOLD_OFF": 21,
    "ITALIC_OFF": 23,
    "FRAKTUR_OFF": 23,
    "LINES_OFF": 24,  # Covers overline, underline, and strikethrough
    "BLINK_OFF": 25,
    "INVERT_OFF": 27,

    "BLACK": 30,
    "RED_DARK": 31,
    "GREEN_DARK": 32,
    "YELLOW_DARK": 33,
    "GOLD": 33,
    "BLUE_DARK": 34,
    "MAGENTA_DARK": 35,
    "CYAN_DARK": 36,
    "GREY": 37,
    "DEFAULT": 39,

    "BG_BLACK": 40,
    "BG_RED_DARK": 41,
    "BG_GREEN_DARK": 42,
    "BG_YELLOW_DARK": 43,
    "BG_BLUE_DARK": 44,
    "BG_MAGENTA_DARK": 45,
    "BG_CYAN_DARK": 46,
    "BG_GREY": 47,
    "BG_DEFAULT": 49,

    "OVERLINE": 53,

    "GREY_DARK": 90,
    "RED": 91,
    "GREEN": 92,
    "YELLOW": 93,
    "BLUE": 94,
    "MAGENTA": 95,
    "CYAN": 96,
    "WHITE": 97,

    "BG_GREY_DARK": 100,
    "BG_RED": 101,
    "BG_GREEN": 102,
    "BG_YELLOW": 103,
    "BG_BLUE": 104,
    "BG_MAGENTA": 105,
    "BG_CYAN": 106,
    "BG_WHITE": 107
}
for (k, v) in defns.items():
    globals()[k] = Ansi((v,))

global RESET, NORMAL, BOLD, FAINT, ITALIC, UNDERLINE, BLINK, BLINK_FAST, INVERT, STRIKETHROUGH, FRAKTUR, BOLD_OFF,\
    ITALIC_OFF, FRAKTUR_OFF, LINES_OFF, BLINK_OFF, INVERT_OFF, BLACK, RED_DARK, GREEN_DARK, YELLOW_DARK,\
    GOLD, BLUE_DARK, MAGENTA_DARK, CYAN_DARK, GREY, DEFAULT, BG_BLACK, BG_RED_DARK, BG_GREEN_DARK, BG_YELLOW_DARK,\
    BG_BLUE_DARK, BG_MAGENTA_DARK, BG_CYAN_DARK, BG_GREY, BG_DEFAULT, OVERLINE, GREY_DARK, RED, GREEN, YELLOW, BLUE,\
    MAGENTA, CYAN, WHITE, BG_GREY_DARK, BG_RED, BG_GREEN, BG_YELLOW, BG_BLUE, BG_MAGENTA, BG_CYAN, BG_WHITE