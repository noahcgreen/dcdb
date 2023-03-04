from __future__ import annotations
import typing as t

import aenum as enum

from dcdb.observe import Observable, ObservableProperty

if t.TYPE_CHECKING:
    from dcdb.engine import Engine
    from dcdb.input import Input
    from dcdb.ability.types import *
    from dcdb.effect.types import *
    from dcdb.types import *


__all__ = ['CharacterType', 'CharacterBehavior', 'Character']


class CharacterType(enum.Flag):
    SUPER_HERO = enum.auto()
    SUPER_VILLAIN = enum.auto()


class CharacterBehavior:

    owner: Character
    attack: t.Optional[Attack]
    defense: t.Optional[Defense]
    manuals: t.List[ManualAbility]
    triggers: t.List[TriggeredAbility]
    effects: t.List[PassiveEffect]

    def __init__(self, owner: Character) -> None:
        self.owner = owner
        self.attack = None
        self.defense = None
        self.manuals = []
        self.triggers = []
        self.effects = []


class Character(Observable):

    id: str
    name: str
    type: CharacterType

    _engine: Engine
    behavior: CharacterBehavior
    manuals: t.List[ManualAbility]
    triggers: t.List[TriggeredAbility]
    effects: t.List[PassiveEffect]
    is_flipped: bool = False
    owner: t.Optional[Player] = None

    options: t.List[Input] = ObservableProperty()

    def __init__(self, engine: Engine, id: str, name: str, type: CharacterType) -> None:
        super().__init__()
        self._engine = engine
        self.id = id
        self.name = name
        self.type = type
        self.behavior = CharacterBehavior(self)
        self.manuals = []
        self.triggers = []
        self.effects = []

        self.options = []

    def __repr__(self) -> str:
        return f'<Character: {self.name}>'

    @property
    def abilities(self) -> t.Iterable[Ability]:
        yield from self.manuals
        yield from self.triggers
        yield from self.effects
