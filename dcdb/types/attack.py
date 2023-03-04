from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from dcdb.event import Event
    from dcdb.input import StateMachine
    from dcdb.types import *

    Owner = t.Union[Card, Character]
    ResolveIndividual = t.Callable[[Player, Player, bool], StateMachine]
    ResolveGroup = t.Callable[[Player, t.List[Player], t.List[Player]], StateMachine]
    Cost = t.Callable[[Event, Player], StateMachine]
    Reward = t.Callable[[Event, Player], StateMachine]


__all__ = ['Attack', 'Defense']


class Attack:

    resolve_individual: ResolveIndividual
    resolve_group: ResolveGroup
    unavoidable: bool

    def __init__(self, resolve_individual: ResolveIndividual, resolve_group: ResolveGroup) -> None:
        self.resolve_individual = resolve_individual
        self.resolve_group = resolve_group
        self.unavoidable = False


class Defense:

    owner: Owner
    range: Region
    cost: Cost
    reward: t.Optional[Reward]

    def __init__(self, owner: Owner, range: Region, cost: Cost, reward: t.Optional[Reward]) -> None:
        self.owner = owner
        self.cost = cost
        self.range = range
        self.reward = reward

    def is_usable(self, owner) -> bool:
        return owner.location.zone.region & self.range


