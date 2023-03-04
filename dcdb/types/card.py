from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

import aenum as enum

from dcdb.observe import Observable, ObservableProperty, Observer
from dcdb.types.location import Location, Region, Zone

if t.TYPE_CHECKING:
    from dcdb.ability.types import *
    from dcdb.effect.types import PassiveEffect
    from dcdb.engine import Engine
    from dcdb.input import Input, StateMachine
    from dcdb.types import *

__all__ = ['Color', 'CardType', 'CardBehavior', 'CardHandle', 'Card']


class Color(enum.Flag):
    NONE = 0
    ALL = ~NONE
    GREEN = enum.auto()
    YELLOW = enum.auto()
    BLUE = enum.auto()
    RED = enum.auto()
    ORANGE = enum.auto()
    GRAY = enum.auto()
    VIOLET = enum.auto()


class CardType(enum.Flag):
    NONE = 0
    ALL = ~NONE

    WEAKNESS = enum.auto()
    STARTER = enum.auto()
    HERO = enum.auto()
    VILLAIN = enum.auto()
    SUPER_POWER = enum.auto()
    EQUIPMENT = enum.auto()
    LOCATION = enum.auto()
    SUPER = enum.auto()
    SUPER_HERO = SUPER | HERO
    SUPER_VILLAIN = SUPER | VILLAIN


class CardBehavior:

    owner: Card
    attack: t.Optional[Attack]
    defense: t.Optional[Defense]
    manuals: t.List[ManualAbility]
    triggers: t.List[TriggeredAbility]
    effects: t.List[PassiveEffect]
    faa: t.Optional[Attack]
    on_play: t.Callable[[Player], StateMachine]
    constant_power: t.Callable[[Player], int]
    star_vp: t.Optional[t.Callable[[Player], int]]
    is_ongoing: bool

    def __init__(self, owner: Card) -> None:
        self.owner = owner
        self.attack = None
        self.defense = None
        self.manuals = []
        self.triggers = []
        self.effects = []
        self.faa = None
        self.on_play = lambda _: iter(())
        self.constant_power = lambda: 0
        self.star_vp = None
        self.is_ongoing = False

    def copy(self, owner: Card) -> CardBehavior:
        copy = CardBehavior(owner)
        copy.attack = self.attack
        copy.defense = self.defense
        copy.manuals = [ability.copy(owner) for ability in self.manuals]
        return copy


@dataclass
class CardHandle:

    card: Card
    is_released: bool = field(default=False, init=False)

    def check_release(self) -> bool:
        if not self:
            return False
        for other in self.card.handles:
            if other != self:
                other.release()
        return True

    def release(self) -> None:
        self.is_released = True

    def __bool__(self) -> bool:
        return not self.is_released

    def __eq__(self, other: CardHandle) -> bool:
        return id(self) == id(other)

    def __ne__(self, other: CardHandle) -> bool:
        return id(self) != id(other)


class Card(Observable):

    id: str
    name: str
    type: CardType
    color: Color
    cost: int
    vp: int

    _engine: Engine
    location: Location
    visibility: set = ObservableProperty()
    behavior: CardBehavior
    temp_behaviors: t.List[CardBehavior]
    owner: t.Optional[Player]
    ongoing_abilities: t.List[Ability]
    handles: t.List[CardHandle]

    options: t.List[Input] = ObservableProperty()

    def __init__(self, engine: Engine, id: str, name: str, type: CardType, color: Color, cost: int, vp: int) -> None:
        super().__init__()
        self.id = id
        self.name = name
        self.type = type
        self.color = color
        self.cost = cost
        self.vp = vp

        self._engine = engine
        self.location = Location(Zone(Region.NONE), 0)
        self.visibility = set()
        self.behavior = CardBehavior(self)
        self.ongoing_abilities = []
        self.temp_behaviors = []
        self.handles = []
        self.owner = None

        self.options = []

    @property
    def behaviors(self) -> t.List[CardBehavior]:
        return [self.behavior, *self.temp_behaviors]

    @property
    def effects(self) -> t.List[PassiveEffect]:
        return [effect for behavior in self.behaviors for effect in behavior.effects]

    @property
    def triggers(self) -> t.List[TriggeredAbility]:
        return [trigger for behavior in self.behaviors for trigger in behavior.triggers]

    @property
    def abilities(self) -> t.Iterable[Ability]:
        yield from self.triggers
        yield from self.effects
        yield from self.ongoing_abilities

    def price(self, player: Player) -> int:
        return self._engine.effects.price(self, player)

    @property
    def is_ongoing(self) -> bool:
        return any(behavior.is_ongoing for behavior in self.behaviors)

    def has_name(self, name: str) -> bool:
        return name == self.name

    def is_copy_of(self, other: Card) -> bool:
        return self.has_name(other.name) or other.has_name(self.name)

    def __repr__(self) -> str:
        return f'<Card: {self.name}>'

    def is_visible_to(self, player: Player) -> bool:
        return player in self.visibility
