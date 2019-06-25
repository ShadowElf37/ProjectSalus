def ANSI(*codes):
    return '\x1b[' + ';'.join(map(str, codes)) + 'm'

RESET = ANSI(0)

NORMAL              = 0
BOLD                = 1
FAINT               = 2
ITALIC              = 3
UNDERLINE           = 4
BLINK               = 5
BLINK_FAST          = 6
INVERT              = 7
STRIKETHROUGH       = 9

FRAKTUR             = 20
BOLD_OFF            = 21
ITALIC_OFF          = 23
LINES_OFF           = 24
BLINK_OFF           = 25
INVERT_OFF          = 27

BLACK               = 30
RED_DARK            = 31
GREEN_DARK          = 32
YELLOW_DARK         = 33
BLUE_DARK           = 34
MAGENTA_DARK        = 35
CYAN_DARK           = 36
GREY                = 37

BG_BLACK            = 40
BG_RED_DARK         = 41
BG_GREEN_DARK       = 42
BG_YELLOW_DARK      = 43
BG_BLUE_DARK        = 44
BG_MAGENTA_DARK     = 45
BG_CYAN_DARK        = 46
BG_GREY             = 47

OVERLINE            = 53

GREY_DARK           = 90
RED                 = 91
GREEN               = 92
YELLOW              = 93
BLUE                = 94
MAGENTA             = 95
CYAN                = 96
WHITE               = 97

BG_GREY_DARK        = 100
BG_RED              = 101
BG_GREEN            = 102
BG_YELLOW           = 103
BG_BLUE             = 104
BG_MAGENTA          = 105
BG_CYAN             = 106
BG_WHITE            = 107
