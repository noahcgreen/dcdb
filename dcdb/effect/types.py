from __future__ import annotations

import typing as t

from dcdb.ability.types import Ability

if t.TYPE_CHECKING:
    from dcdb.types import *

    Owner = t.Union[Card, Character]
    Applies = t.Callable[[Card, Player], bool]


__all__ = ['PassiveEffect', 'AlterPower', 'AlterPrice', 'RestrictEvent', 'AlterType',
           'AlterColor', 'AlterName']


class PassiveEffect(Ability):

    applies: Applies

    def __init__(self, owner: Owner, applies: Applies, max_uses: t.Optional[int] = None) -> None:
        super().__init__(owner, max_uses=max_uses)
        self.applies = applies


class AlterPower(PassiveEffect):

    def __init__(self, owner: Owner, applies: Applies, alter) -> None:
        super().__init__(owner, applies)
        self.alter = alter


class AlterPrice(PassiveEffect):

    def __init__(self, owner, applies, price, max_uses=None) -> None:
        super().__init__(owner, applies, max_uses=max_uses)
        self.price = price


class RestrictEvent(PassiveEffect):

    def __init__(self, owner, applies, event_type) -> None:
        super().__init__(owner, applies)
        self.type = event_type


class AlterType(PassiveEffect):

    def __init__(self, owner, applies, added, removed) -> None:
        super().__init__(owner, applies)
        self.added = added
        self.removed = removed


class AlterColor(PassiveEffect):

    def __init__(self, owner, applies, added, removed) -> None:
        super().__init__(owner, applies)
        self.added = added
        self.removed = removed


class AlterName(PassiveEffect):

    def __init__(self, owner, applies, has_name) -> None:
        super().__init__(owner, applies)
        self.has_name = has_name
