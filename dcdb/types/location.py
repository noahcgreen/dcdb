from __future__ import annotations

import typing as t
from dataclasses import dataclass

import aenum as enum

from dcdb.observe import ObservableCollection

if t.TYPE_CHECKING:
    from dcdb.engine import Engine
    from dcdb.types.card import Card
    from dcdb.types.player import Player


__all__ = ['Region', 'Zone', 'Location', 'Pile']


class Region(enum.Flag):
    NONE = 0
    ALL = ~NONE

    MAIN_DECK = enum.auto()
    LINE_UP = enum.auto()
    KICK_STACK = enum.auto()
    WEAKNESS_STACK = enum.auto()
    SV_STACK = enum.auto()
    DESTROYED_PILE = enum.auto()

    DECK = enum.auto()
    HAND = enum.auto()
    IN_PLAY = enum.auto()
    DISCARD_PILE = enum.auto()

    OVER_CHARACTER = enum.auto()
    UNDER_CHARACTER = enum.auto()

    UNDER_CARD = enum.auto()


@dataclass(frozen=True)
class Zone:
    region: Region
    player: t.Optional[Player] = None
    card: t.Optional[Card] = None


@dataclass(frozen=True)
class Location:
    zone: Zone
    index: int


class Pile(ObservableCollection['Card']):

    _engine: Engine
    zone: Zone
    _cards: t.MutableSequence[Card]

    def __init__(self, engine: Engine, zone: Zone) -> None:
        super().__init__()
        self._engine = engine
        self.zone = zone
        self._cards = []

    def __getitem__(self, index: int) -> Card:
        return self._cards[index]

    def __setitem__(self, index: int, card: Card) -> None:
        self._cards[index] = card
        card.location = Location(self.zone, index)
        super().__setitem__(index, card)

    def __delitem__(self, index: int) -> None:
        del self._cards[index]
        i = index
        while i < len(self):
            self[i].location = Location(self.zone, i)
            i += 1
        super().__delitem__(index)

    def __len__(self) -> int:
        return len(self._cards)

    def __repr__(self):
        return f'<Pile: {self.zone}>'

    def insert(self, index: int, card: Card) -> None:
        self._cards.insert(index, card)
        i = index
        super().insert(index, card)
        while i < len(self):
            self[i].location = Location(self.zone, i)
            i += 1
