from __future__ import annotations

import itertools
import typing as t

import dcdb
from dcdb.observe import ObservableCollection
from dcdb.types.location import Pile, Region, Zone

if t.TYPE_CHECKING:
    from dcdb.ability.types import *
    from dcdb.effect.types import *
    from dcdb.engine import Engine
    from dcdb.types import *


__all__ = ['Player']


class CharacterList(ObservableCollection['Character']):

    _characters: t.List[Character]

    def __init__(self) -> None:
        super().__init__()
        self._characters = []

    def __getitem__(self, item: int) -> Character:
        return self._characters[item]

    def __setitem__(self, key: int, value: Character) -> None:
        self._characters[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key: int) -> None:
        del self._characters[key]
        super().__delitem__(key)

    def __len__(self):
        return len(self._characters)

    def insert(self, index: int, object: Character) -> None:
        self._characters.insert(index, object)
        super().insert(index, object)


class Player:

    _engine: Engine
    index: int

    characters: t.MutableSequence[Character]

    hand: Pile
    deck: Pile
    in_play: Pile
    discard: Pile
    over_character: Pile
    under_character: Pile
    temp_triggers: t.List[TriggeredAbility]
    temp_manuals: t.List[ManualAbility]
    temp_effects: t.List[PassiveEffect]

    def __init__(self, engine: Engine, index: int) -> None:
        self._engine = engine
        self.index = index
        self.characters = CharacterList()
        self.hand = Pile(engine, Zone(Region.HAND, self))
        self.deck = Pile(engine, Zone(Region.DECK, self))
        self.in_play = Pile(engine, Zone(Region.IN_PLAY, self))
        self.discard = Pile(engine, Zone(Region.DISCARD_PILE, self))
        self.over_character = Pile(engine, Zone(Region.OVER_CHARACTER, self))
        self.under_character = Pile(engine, Zone(Region.UNDER_CHARACTER, self))
        self.temp_triggers = []
        self.temp_manuals = []
        self.temp_effects = []

    def __repr__(self) -> str:
        return f'<Player: {self.index}>'

    @property
    def cards(self) -> t.Iterable[Card]:
        # Doesn't account for owned cards in foe's control
        return itertools.chain(self.hand, self.deck, self.in_play, self.discard)

    @property
    def foes(self) -> t.List[Player]:
        return [
            self._engine.players[(i + self.index) % len(self._engine.players)]
            for i in range(1, len(self._engine.players))
        ]

    @property
    def left_foe(self) -> Player:
        return self._engine.players[(self.index + 1) % len(self._engine.players)]

    @property
    def right_foe(self) -> Player:
        return self._engine.players[(self.index - 1) % len(self._engine.players)]

    @property
    def controlled(self) -> t.Iterable[Card]:
        # TODO: Account for Swamp Thing etc.
        return list(self.in_play)

    @property
    def defenses(self) -> t.Iterable[Defense]:
        for card in self.cards:
            for behavior in card.behaviors:
                if behavior.defense and behavior.defense.is_usable(card):
                    yield behavior.defense

    @property
    def vp(self) -> int:
        def _vp(card: Card) -> int:
            return card.behavior.star_vp(self) if card.behavior.star_vp else card.vp
        return sum(_vp(card) for card in self.deck)
