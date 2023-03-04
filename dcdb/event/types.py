from __future__ import annotations

import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import aenum as enum
from dcdb.input import State, SelectionInput
from dcdb.types import Region

if t.TYPE_CHECKING:
    from dcdb.input import StateMachine
    from dcdb.types import *


if t.TYPE_CHECKING:
    from dcdb.engine import Engine

    Destination = t.Union[Location, Pile]


__all__ = ['EventType', 'Event', 'MoveEvent', 'RevealEvent', 'GainEvent', 'BuyEvent',
           'DestroyEvent', 'DiscardEvent', 'DrawEvent', 'PlayEvent', 'AttackIndividualEvent',
           'AttackGroupEvent', 'AttackEvent', 'PowerEvent', 'AbilityEvent', 'TurnStartEvent',
           'TurnEndEvent', 'GameEndEvent', 'DiscardToDeckEvent']


class EventType(enum.Flag):

    @classmethod
    def _next_value(cls) -> int:
        if not len(cls):
            return 1
        return 2 ** max(len(format(m.value, 'b')) for m in cls)

    @classmethod
    def register(cls, name: str) -> t.Callable[[t.Type[Event]], t.Type[Event]]:
        enum.extend_enum(cls, name, cls._next_value())
        event_type = cls[name]

        def decorated(event_class: t.Type[Event]) -> t.Type[Event]:
            setattr(event_class, 'type', property(lambda instance: event_type))
            return event_class

        return decorated


@dataclass
class Event(ABC):

    _engine: Engine = field(repr=False)
    type: EventType = field(init=False, repr=False)
    parent: t.Optional[Event] = field(default=None, init=False, repr=False)

    @abstractmethod
    def _dispatch(self) -> StateMachine:
        pass

    def ancestor(self, type: EventType) -> t.Optional[Event]:
        if not self.parent:
            return None
        return self.parent if self.parent.type & type else self.parent.ancestor(type)


@EventType.register('MOVE')
@dataclass
class MoveEvent(Event):

    card: Card
    destination: Destination
    # TODO: Make it possible to track all card state per event? Previous location, types, etc.
    origin: Location = field(init=False)
    visibility: t.Optional[t.Set[Player]] = field(default=None)

    def __post_init__(self):
        self.origin = self.card.location

        if self.visibility is None:
            public_zones = (Region.LINE_UP | Region.KICK_STACK | Region.WEAKNESS_STACK | Region.DESTROYED_PILE
                            | Region.IN_PLAY | Region.DISCARD_PILE | Region.OVER_CHARACTER)
            if self.destination.zone.region & public_zones:
                self.visibility = set(self._engine.players)
            elif self.destination.zone.region & Region.HAND:
                self.visibility = {self.destination.zone.player}
            else:
                self.visibility = set()

    def _dispatch(self) -> StateMachine:
        current_pile = self._engine.cards_at(self.card.location.zone)
        try:
            # Pile
            index = len(self.destination)
            to_pile = self.destination
        except TypeError:
            # Location
            index = self.destination.index
            to_pile = self._engine.cards_at(self.destination.zone)

        if current_pile:
            current_pile.remove(self.card)
        to_pile.insert(index, self.card)
        self.card.visibility = self.visibility
        yield from ()


@EventType.register('REVEAL')
@dataclass
class RevealEvent(Event):

    cards: t.Iterable[Card]
    player: t.Iterable[Player]

    def _dispatch(self) -> StateMachine:
        yield from ()


@EventType.register('GAIN')
@dataclass
class GainEvent(Event):

    card: Card
    player: Player
    destination: t.Optional[Destination]

    @property
    def _default_destination(self) -> Destination:
        return self.player.discard

    def _dispatch(self) -> StateMachine:
        destination = self.destination or self._default_destination
        self.card.owner = self.player
        move = MoveEvent(self._engine, self.card, destination)
        yield from self._engine.events.dispatch(move)


@EventType.register('BUY')
@dataclass
class BuyEvent(Event):

    card: Card
    buyer: Player

    def _dispatch(self) -> StateMachine:
        self._engine.current_turn.power -= self.card.price(self.buyer)
        gain = GainEvent(self._engine, self.card, self.buyer, self.buyer.discard)
        yield from self._engine.events.dispatch(gain)


@EventType.register('DESTROY')
@dataclass
class DestroyEvent(Event):

    card: Card
    destroyer: Player

    def _dispatch(self) -> StateMachine:
        if self.card.owner and self.card.owner != self.destroyer:
            destination = self.card.owner.discard
        else:
            self.card.owner = None
            destination = self._engine.destroyed_pile
        move = MoveEvent(self._engine, self.card, destination)
        yield from self._engine.events.dispatch(move)


@EventType.register('DISCARD')
@dataclass
class DiscardEvent(Event):

    card: Card

    def _dispatch(self) -> StateMachine:
        move = MoveEvent(self._engine, self.card, self.card.owner.discard)
        yield from self._engine.events.dispatch(move)


@EventType.register('DISCARD_TO_DECK')
@dataclass
class DiscardToDeckEvent(Event):

    player: Player

    def _dispatch(self) -> StateMachine:
        cards = list(self.player.discard)
        # self.player.discard.clear()
        self._engine.random.shuffle(cards)
        for card in cards:
            move = MoveEvent(self._engine, card, self.player.deck)
            yield from self._engine.events.dispatch(move)


@EventType.register('DRAW')
@dataclass
class DrawEvent(Event):

    player: Player
    amount: int

    def _dispatch(self) -> StateMachine:
        if len(self.player.deck) < self.amount:
            shuffle = DiscardToDeckEvent(self._engine, self.player)
            yield from self._engine.events.dispatch(shuffle)
        for _ in range(self.amount):
            if self.player.deck:
                move = MoveEvent(self._engine, self.player.deck[0], self.player.hand)
                yield from self._engine.events.dispatch(move)
            else:
                break


@EventType.register('PLAY')
@dataclass
class PlayEvent(Event):

    player: Player
    card: Card

    def _dispatch(self) -> StateMachine:
        if self.card not in self.player.in_play:
            move = MoveEvent(self._engine, self.card, self.player.in_play)
            yield from self._engine.events.dispatch(move)
        i = 0
        while i < len(self.card.behaviors):
            on_play = self.card.behaviors[i].on_play
            if on_play:
                def _dispatch_(e: AbilityEvent) -> StateMachine:
                    yield from on_play(self.player)
                yield from self._engine.events.dispatch(AbilityEvent(self._engine, self.card, self.player, _dispatch_))
            i += 1


@EventType.register('ATTACK_INDIVIDUAL')
@dataclass
class AttackIndividualEvent(Event):

    attacker: t.Optional[Player]
    attack: Attack
    target: Player
    victims: t.List[Player]
    defenders: t.List[Player]

    def _dispatch(self) -> StateMachine:
        defended = False
        defense = None

        if not self.attack.unavoidable:
            options = list(map(SelectionInput, self.target.defenses))
            if options:
                options.insert(0, SelectionInput(None))
                input = yield State(self.target, options, 'You may use a Defense')
                if input.selection:
                    defended = True
                    defense = input.selection

        if defended:
            self.defenders.append(self.target)
            yield from defense.cost(self, self.target)
            if defense.reward:
                yield from defense.reward(self, self.target)
        else:
            self.victims.append(self.target)
        yield from self.attack.resolve_individual(self.attacker, self.target, defended)


@EventType.register('ATTACK_GROUP')
@dataclass
class AttackGroupEvent(Event):

    attacker: t.Optional[Player]
    attack: Attack
    victims: t.List[Player]
    defenders: t.List[Player]

    def _dispatch(self) -> StateMachine:
        yield from self.attack.resolve_group(self.attacker, self.victims, self.defenders)


@EventType.register('ATTACK')
@dataclass
class AttackEvent(Event):

    attacker: t.Optional[Player]
    attack: Attack
    targets: t.List[Player]
    victims: t.List[Player] = field(default_factory=list, init=False)
    defenders: t.List[Player] = field(default_factory=list, init=False)

    def _dispatch(self) -> StateMachine:
        for target in self.targets:
            individual = AttackIndividualEvent(self._engine, self.attacker, self.attack, target, self.victims, self.defenders)
            yield from self._engine.events.dispatch(individual)
        group = AttackGroupEvent(self._engine, self.attacker, self.attack, self.victims, self.defenders)
        yield from self._engine.events.dispatch(group)


@EventType.register('POWER')
@dataclass
class PowerEvent(Event):

    player: Player
    amount: t.Callable[[Player], int]

    def _dispatch(self) -> StateMachine:
        if self._engine.current_turn and self._engine.turn_player == self.player:
            amount = self.amount(self.player)
            self._engine.current_turn.power += amount
        yield from ()


@EventType.register('ABILITY')
@dataclass
class AbilityEvent(Event):

    owner: t.Union[Card, Character]
    controller: Player
    _dispatch_: t.Callable[[AbilityEvent], StateMachine] = field(repr=False)

    def _dispatch(self) -> StateMachine:
        yield from self._dispatch_(self)


@EventType.register('TURN_START')
@dataclass
class TurnStartEvent(Event):

    player: Player

    def _dispatch(self) -> StateMachine:
        yield from ()


@EventType.register('TURN_END')
@dataclass
class TurnEndEvent(Event):

    player: Player

    def _dispatch(self) -> StateMachine:
        yield from ()


@EventType.register('GAME_END')
@dataclass
class GameEndEvent(Event):

    def _dispatch(self) -> StateMachine:
        yield from ()
