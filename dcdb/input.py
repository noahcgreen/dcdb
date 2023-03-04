from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
import typing as t

if t.TYPE_CHECKING:
    from .types import Card, Player

T = t.TypeVar('T')

__all__ = ['Input', 'PlayInput', 'BuyInput', 'EndTurnInput',
           'SelectionInput', 'State']


@dataclass(frozen=True)
class Input(ABC):
    pass


@dataclass(frozen=True)
class PlayInput(Input):
    card: Card


@dataclass(frozen=True)
class BuyInput(Input):
    card: Card


@dataclass(frozen=True)
class EndTurnInput(Input):
    pass


@dataclass(frozen=True)
class SelectionInput(Input, t.Generic[T]):
    selection: T


@dataclass(frozen=True)
class State:
    active_player: t.Optional[Player]
    options: t.List[Input]
    hint: t.Optional[str] = None


if t.TYPE_CHECKING:
    StateMachine = t.Generator[State, Input, None]
    __all__.append('StateMachine')
