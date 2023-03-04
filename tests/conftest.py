from __future__ import annotations

import logging
from pathlib import Path
import typing as t

import pytest

from dcdb.game import Game
from dcdb.input import *
from dcdb.input import Input

if t.TYPE_CHECKING:
    from dcdb.types import *


# @pytest.fixture(autouse=True)
# def log_level(caplog):
#     caplog.set_level(logging.DEBUG)


@pytest.fixture
def set_dir():
    return Path('../sets/')


@pytest.fixture
def script_dir():
    return Path('../scripts/')


class _GameDriver:

    game: Game

    def __init__(self, game: Game):
        self.game = game

    def start(self):
        self.game.start()

    def process(self, predicate: t.Callable[[Input], bool]):
        for i, option in enumerate(self.game.options):
            if predicate(option):
                self.game.process(i)
                return option
        raise ValueError('No valid option for predicate')

    def cancel(self):
        self.select(lambda selection: not selection)

    def end_turn(self):
        self.process(lambda option: isinstance(option, EndTurnInput))

    def play(self, name: str) -> Card:
        def pred(option: Input) -> bool:
            return isinstance(option, PlayInput) and option.card.name == name
        return t.cast(PlayInput, self.process(pred)).card

    def select(self, predicate):
        def pred(option: Input) -> bool:
            return isinstance(option, SelectionInput) and predicate(option.selection)
        return t.cast(SelectionInput, self.process(pred)).selection

    def buy(self, name: str) -> Card:
        def pred(option: Input) -> bool:
            return isinstance(option, BuyInput) and option.card.name == name
        return t.cast(BuyInput, self.process(pred)).card


@pytest.fixture
def Driver():
    return _GameDriver
