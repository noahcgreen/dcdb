from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from dcdb.event.types import Event, EventType
    from dcdb.input import StateMachine
    from dcdb.types import *

    Owner = t.Union[Card, Character]
    ActivateManual = t.Callable[[Player], StateMachine]
    CanActivate = t.Callable[[Player], bool]
    Responds = t.Callable[[Event, Player], bool]
    ActivateTrigger = t.Callable[[Event, Player], StateMachine]


__all__ = ['Ability', 'ManualAbility', 'TriggeredAbility']


class Ability:

    owner: Owner
    range: t.Optional[Region]
    max_uses: t.Optional[int]
    remaining_uses: t.Optional[int]

    def __init__(self, owner: Owner, max_uses: t.Optional[int] = None) -> None:
        self.owner = owner
        self.range = None
        self.max_uses = max_uses
        self.remaining_uses = max_uses

    @property
    def is_in_range(self) -> bool:
        return not self.range or self.owner.location.zone.region & self.range

    @property
    def is_usable(self) -> bool:
        try:
            if self.owner.is_flipped:
                return False
        except AttributeError:
            pass
        has_uses = self.remaining_uses is None or self.remaining_uses > 0
        return has_uses and self.is_in_range

    def use(self) -> None:
        if self.remaining_uses is not None:
            self.remaining_uses -= 1

    def reset(self) -> None:
        self.remaining_uses = self.max_uses


class ManualAbility(Ability):

    activate: ActivateManual
    can_activate: CanActivate

    def __init__(self, owner: Owner, activate: ActivateManual, max_uses: t.Optional[int] = None) -> None:
        super().__init__(owner, max_uses=max_uses)
        self.activate = activate
        self.can_activate = lambda activator: True

    def copy(self, owner: Owner) -> ManualAbility:
        copy = ManualAbility(owner, self.activate)
        copy.range = self.range
        copy.max_uses = self.max_uses
        copy.can_activate = self.can_activate
        copy.reset()
        return copy


class TriggeredAbility(Ability):

    type: EventType
    responds: Responds
    activate: ActivateTrigger
    is_preemptive: bool
    is_immediate: bool
    is_optional: bool

    def __init__(self, owner: Owner, type: EventType, responds: Responds, activate: ActivateTrigger, max_uses: t.Optional[int] = None) -> None:
        super().__init__(owner, max_uses=max_uses)
        self.type = type
        self.responds = responds
        self.activate = activate
        self.is_preemptive = False
        self.is_immediate = False
        self.is_optional = False
