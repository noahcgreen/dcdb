from dcdb.input import *
from dcdb.types import *


def option_name(option):
    if isinstance(option, PlayInput):
        return 'Play'
    if isinstance(option, BuyInput):
        return 'Buy'
    if isinstance(option, SelectionInput) and isinstance(option.selection, Defense):
        return 'Defend'
    if isinstance(option, SelectionInput) and isinstance(option.selection, Card):
        return 'Select'
