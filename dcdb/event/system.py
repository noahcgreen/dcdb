from __future__ import annotations

import typing as t
from collections import deque
from dataclasses import dataclass, field
from dcdb.observe import Observable

if t.TYPE_CHECKING:
    from dcdb.ability.types import TriggeredAbility
    from dcdb.engine import Engine
    from dcdb.event.types import Event
    from dcdb.input import StateMachine
    from dcdb.types import *


__all__ = ['EventSystem']


@dataclass
class _AbilityTuple:

    preemptives: t.List = field(default_factory=list)
    immediates: t.List = field(default_factory=list)
    regulars: t.List = field(default_factory=list)


class EventHandler:

    def pre_event(self, event: Event) -> StateMachine:
        yield from ()

    def post_event(self, event: Event) -> StateMachine:
        yield from ()


class EventSystem(Observable):

    _engine: Engine
    _pending: t.Dict[Player, t.List[t.Tuple[TriggeredAbility, Event]]]
    _enabled: bool
    _stack: deque
    handlers: t.List[EventHandler]
    log: t.List[Event]

    def __init__(self, engine: Engine) -> None:
        super().__init__()
        self._engine = engine
        self._stack = deque()
        self.handlers = []
        self.log = []

    def dispatch(self, event: Event) -> StateMachine:
        if self._stack:
            event.parent = self._stack[-1]

        self.notify('event_start', event)

        for handler in reversed(self.handlers):
            yield from handler.pre_event(event)

        self._stack.append(event)
        yield from event._dispatch()
        self._stack.pop()

        self.log.append(event)

        self.notify('event_end', event)

        for handler in reversed(self.handlers):
            yield from handler.post_event(event)
