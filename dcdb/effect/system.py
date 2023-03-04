from __future__ import annotations

import typing as t

from dcdb.effect.types import *

if t.TYPE_CHECKING:
    from dcdb.engine import Engine
    from dcdb.types import *

    Effect = t.TypeVar('Effect', bound=PassiveEffect)


class EffectSystem:

    engine: Engine

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def card_effects(self, card: Card, type: t.Type[Effect]) -> t.Iterable[Effect]:
        return filter(lambda effect: isinstance(effect, type), card.effects)

    def character_effects(self, character: Character, type: t.Type[Effect]) -> t.Iterable[Effect]:
        return filter(lambda effect: isinstance(effect, type), character.effects)

    def player_effects(self, player: Player, type: t.Type[Effect]) -> t.Iterable[Effect]:
        for character in player.characters:
            yield from self.character_effects(character, type)
        yield from player.temp_effects
        for card in player.controlled:
            yield from self.card_effects(card, type)
        for card in (*self.engine.line_up, *self.engine.destroyed_pile):
            yield from self.card_effects(card, type)

    def price(self, card: Card, player: Player) -> int:
        price = card.cost
        for effect in self.player_effects(player, AlterPrice):
            if effect.applies(card, player) and effect.is_usable:
                price = effect.price(card, player, price)
        return price
