from __future__ import annotations

import collections
import itertools
import logging
import random
import sys
import typing as t

from .ability.system import AbilitySystem
from .ability.types import TriggeredAbility
from .effect.system import EffectSystem
from .effect.types import PassiveEffect
from .event.system import EventSystem
from .input import *
from .observe import *
from .routines import GameLoop
from .scripting.interpreter import LuaInterpreter
from .loaders import SetLoader
from .types import *

if t.TYPE_CHECKING:
    import os

    from .routines import Turn

    PathLike = t.Union[str, bytes, os.PathLike]


__all__ = ['Engine']


class Engine(Observable, Observer):

    LINE_UP_CAPACITY: int = 5

    _shuffle: bool
    _loader: SetLoader

    loop: GameLoop
    state: t.Optional[State] = ObservableProperty()
    random: random.Random
    abilities: AbilitySystem
    effects: EffectSystem
    events: EventSystem
    interpreter: LuaInterpreter
    logger: logging.Logger

    main_deck: Pile
    line_up: Pile
    kick_stack: Pile
    weakness_stack: Pile
    sv_stack: Pile
    destroyed_pile: Pile
    removed: Pile

    players: t.List[Player]

    passives: t.List[PassiveEffect]

    _card_options: t.Dict[Card, t.List[Input]]

    def __init__(self, set_path: PathLike, seed: t.Optional[int], logger: logging.Logger,
                 shuffle: bool = False, script_dir: PathLike = '.') -> None:
        super().__init__()
        self.logger = logger
        self.register(self)
        self._shuffle = shuffle
        self.loop = GameLoop(self)
        self.state = None

        seed = seed or random.randint(0, sys.maxsize)
        self.random = random.Random()
        self.random.seed(seed)
        self._loader = SetLoader(self, set_path, script_dir)
        self.events = EventSystem(self)
        self.abilities = AbilitySystem(self)
        self.effects = EffectSystem(self)
        self.events.handlers.append(self.abilities)
        self.interpreter = LuaInterpreter(self, seed)

        self.main_deck = Pile(self, Zone(Region.MAIN_DECK))
        self.line_up = Pile(self, Zone(Region.LINE_UP))
        self.kick_stack = Pile(self, Zone(Region.KICK_STACK))
        self.weakness_stack = Pile(self, Zone(Region.WEAKNESS_STACK))
        self.sv_stack = Pile(self, Zone(Region.SV_STACK))
        self.destroyed_pile = Pile(self, Zone(Region.DESTROYED_PILE))
        self.removed = Pile(self, Zone(Region.NONE))

        self.players = []

        self.passives = []

        self._card_options = {}

        self._load_set()

    def observe_state(self, game):
        if not self.state:
            return

        for card in self._card_options.keys():
            card.options = []

        options = collections.defaultdict(list)
        for option in self.state.options:
            if isinstance(option, PlayInput) or isinstance(option, BuyInput):
                card = option.card
            elif isinstance(option, SelectionInput) and isinstance(option.selection, Card):
                card = option.selection
            elif isinstance(option, SelectionInput) and isinstance(option.selection, Defense) and isinstance(option.selection.owner, Card):
                card = option.selection.owner
            elif isinstance(option, SelectionInput) and isinstance(option.selection, TriggeredAbility) and isinstance(option.selection.owner, Card):
                card = option.selection.owner
            else:
                card = None
            if card:
                options[card].append(option)

        self._card_options = dict(options)
        for card, ops in options.items():
            card.options = ops

    def add_player(self, *characters: str) -> Player:
        self.logger.debug('Adding player')
        player = Player(self, len(self.players))

        for character in characters:
            self.logger.debug(f'Building character {character}')
            player.characters.append(self._loader.build_character(character))

        self.logger.debug('Building starters')
        starters = self._loader.build_starters()
        for card in starters:
            card.owner = player
        if self._shuffle:
            self.logger.debug('Shuffling starters')
            self.random.shuffle(starters)
        player.deck.extend(starters)

        self.players.append(player)
        self.logger.info('Added player %s', player)
        return player

    def _load_set(self) -> None:
        self.logger.debug('Loading set')
        main_deck = self._loader.build_main_deck()
        kicks = self._loader.build_kicks()
        weaknesses = self._loader.build_weaknesses()
        sv_top = self._loader.build_sv_top()
        sv_middle = self._loader.build_sv_middle()

        if self._shuffle:
            self.logger.debug('Shuffling set')
            for seq in (main_deck, kicks, weaknesses, sv_top, sv_middle):
                self.random.shuffle(seq)

        self.main_deck.extend(main_deck)
        self.kick_stack.extend(kicks)
        self.weakness_stack.extend(weaknesses)
        self.sv_stack.extend(sv_top)
        self.sv_stack.extend(sv_middle)

        self.logger.info('Loaded set')

    @property
    def is_over(self) -> bool:
        return not self.state.options

    def start(self) -> None:
        self.logger.debug('Starting game')
        for card in itertools.chain(self.kick_stack, self.weakness_stack):
            card.visibility = set(self.players)
        if self.sv_stack:
            self.sv_stack[0].visibility = set(self.players)
        self.state = next(self.loop)
        self.logger.info('Started game')

    def process(self, index: int) -> None:
        input = self.state.options[index]
        self.logger.debug('Processing input %s', input)
        try:
            self.state = self.loop.send(input)
        except StopIteration:
            self.logger.debug('Input led to terminal state')
            self.state = State(None, [])
        else:
            self.logger.info('Finished processing input %s', input)

    @property
    def current_turn(self) -> Turn:
        return self.loop.turns.current_turn

    @property
    def turn_player(self) -> Player:
        if not self.current_turn:
            return self.loop.turns.log[-1].player
        return self.current_turn.player

    @property
    def cards(self) -> t.Iterable[Card]:
        for player in self.players:
            yield from player.cards
        yield from itertools.chain(
            self.line_up,
            self.sv_stack,
            self.main_deck,
            self.kick_stack,
            self.weakness_stack,
            self.destroyed_pile
        )

    @property
    def characters(self) -> t.Iterable[Character]:
        for player in self.players:
            yield from player.characters

    def cards_at(self, zone) -> t.Optional[Pile]:
        if zone.region == Region.NONE:
            return self.removed
        elif zone.region == Region.MAIN_DECK:
            return self.main_deck
        elif zone.region == Region.LINE_UP:
            return self.line_up
        elif zone.region == Region.KICK_STACK:
            return self.kick_stack
        elif zone.region == Region.WEAKNESS_STACK:
            return self.weakness_stack
        elif zone.region == Region.SV_STACK:
            return self.sv_stack
        elif zone.region == Region.DESTROYED_PILE:
            return self.destroyed_pile
        elif zone.region == Region.DECK:
            return zone.player.deck
        elif zone.region == Region.HAND:
            return zone.player.hand
        elif zone.region == Region.IN_PLAY:
            return zone.player.in_play
        elif zone.region == Region.DISCARD_PILE:
            return zone.player.discard
        elif zone.region == Region.OVER_CHARACTER:
            return zone.player.over_character
        elif zone.region == Region.UNDER_CHARACTER:
            return zone.player.under_character
