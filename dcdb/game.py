from __future__ import annotations
import typing as t

import logging

from .engine import Engine
from .input import Input
from .observe import *
from .types import *

if t.TYPE_CHECKING:
    from .engine import PathLike

__all__ = ['Game']

logger = logging.getLogger(__name__)


class GameLoggerAdapter(logging.LoggerAdapter):

    def process(self, msg, kwargs):
        kwargs['extra'] = {'game': self.extra['game']}
        return msg, kwargs


class Game(Observable, Observer):

    _engine: Engine

    def __init__(self,
                 set_path: PathLike,
                 seed: t.Optional[int] = None,
                 shuffle: bool = True,
                 script_dir: PathLike = '.'
                 ) -> None:
        super().__init__()
        self._engine = Engine(set_path, seed, GameLoggerAdapter(logger, {'game': self}), shuffle, script_dir=script_dir)

        self._engine.register(self)
        self._engine.events.register(self)
        self._engine.loop.turns.register(self)

    def observe_event_start(self, obj, event):
        self.notify('event_start', event)

    def observe_event_end(self, obj, event):
        self.notify('event_end', event)

    def observe_state(self, obj):
        self.notify('options')
        self.notify('active_player')
        self.notify('hint')

    def observe_current_turn(self, loop):
        if loop.current_turn:
            loop.current_turn.register(self)
        self.notify('turn_player')
        self.notify('power')

    def observe_power(self, turn):
        self.notify('power')

    def add_player(self, *characters: str) -> Player:
        return self._engine.add_player(*characters)

    @property
    def auto_resolution_order(self) -> bool:
        """
        If auto resolution order is enabled, the game will decide the order in
        which triggered abilities are resolved. If disabled, the active player
        will be prompted to select which ability should resolve before the
        others.

        Additionally, if auto resolution order is enabled, the game will
        always resolve optional triggered abilities.
        """
        return self._engine.abilities.auto_order

    @auto_resolution_order.setter
    def auto_resolution_order(self, enabled: bool) -> None:
        self._engine.abilities.auto_order = enabled

    def start(self):
        self._engine.start()

    def process(self, input: t.Union[Input, int]) -> None:
        if isinstance(input, Input):
            input = self.options.index(input)
        self._engine.process(input)

    @property
    def is_over(self) -> bool:
        return self._engine.is_over

    @property
    def active_player(self) -> Player:
        return self._engine.state.active_player

    @property
    def turn_player(self) -> t.Optional[Player]:
        if self._engine.current_turn:
            return self._engine.current_turn.player

    @property
    def options(self) -> t.Sequence[Input]:
        return self._engine.state.options if self._engine.state else []

    @property
    def hint(self) -> t.Optional[str]:
        return self._engine.state.hint if self._engine.state else None

    @property
    def players(self) -> t.Sequence[Player]:
        return self._engine.players

    @property
    def main_deck(self) -> t.Sequence[Card]:
        return self._engine.main_deck

    @property
    def line_up(self) -> t.Sequence[Card]:
        return self._engine.line_up

    @property
    def kick_stack(self) -> t.Sequence[Card]:
        return self._engine.kick_stack

    @property
    def weakness_stack(self) -> t.Sequence[Card]:
        return self._engine.weakness_stack

    @property
    def sv_stack(self) -> t.Sequence[Card]:
        return self._engine.sv_stack

    @property
    def destroyed_pile(self) -> t.Sequence[Card]:
        return self._engine.destroyed_pile

    @property
    def power(self) -> int:
        return self._engine.current_turn.power if self._engine.current_turn else 0

    def cards_at(self, zone: Zone) -> t.Optional[t.Sequence[Card]]:
        return self._engine.cards_at(zone)