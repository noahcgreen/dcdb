from __future__ import annotations

import typing as t
from collections import defaultdict
from dcdb.ability.types import TriggeredAbility
from dcdb.event.types import AbilityEvent, Event
from dcdb.input import SelectionInput, State

if t.TYPE_CHECKING:
    from dcdb.engine import Engine
    from dcdb.input import StateMachine
    from dcdb.types import Player


__all__ = ['AbilitySystem']


class AbilitySystem:

    engine: Engine
    pending: t.Dict[Player, t.List[t.Tuple[TriggeredAbility, Event]]]
    enabled: bool = False
    auto_order: bool = True

    # TODO: Track available abilities instead of searching entire game state every time
    # _triggers_: t.Dict[Player, TriggeredAbility]

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.pending = defaultdict(list)

    @property
    def players(self) -> t.List[Player]:
        player = self.engine.turn_player.left_foe
        players = []
        while player not in players:
            players.append(player)
            player = player.left_foe
        return players

    def reset(self) -> None:
        for card in self.engine.cards:
            for ability in card.abilities:
                ability.reset()
        for character in self.engine.characters:
            for ability in character.abilities:
                ability.reset()

    def _triggers(self, player: Player) -> t.Iterable[TriggeredAbility]:
        public = [*self.engine.line_up, *self.engine.destroyed_pile]
        discard = (ability for card in player.discard for ability in card.triggers if ability.is_in_range)
        for character in player.characters:
            yield from character.triggers
        yield from player.temp_triggers
        for card in player.controlled:
            yield from filter(lambda ability: isinstance(ability, TriggeredAbility), card.ongoing_abilities)
        yield from discard
        if self.engine.sv_stack:
            yield from self.engine.sv_stack[0].triggers
        for card in public:
            yield from card.triggers

    def mark_pending(self, event: Event) -> None:
        for player in self.players:
            self.pending[player].extend([
                (ability, event)
                for ability in self._triggers(player)
                if ability.type & event.type == event.type
                if ability.responds(event, player)
                if not (ability.is_preemptive or ability.is_immediate)
            ])

    def resolve(self, ability: TriggeredAbility, event: Event, controller: t.Optional[Player]) -> StateMachine:
        def _dispatch_(_: AbilityEvent) -> StateMachine:
            ability.use()
            yield from ability.activate(event, controller)

        ability_event = AbilityEvent(self.engine, ability.owner, controller, _dispatch_)
        yield from self.engine.events.dispatch(ability_event)

    def resolve_multiple(self, abilities: t.Iterable[t.Tuple[TriggeredAbility, Event]], controller: t.Optional[Player]) -> StateMachine:
        abilities = [
            (ability, event)
            for ability, event in abilities
            if ability.is_usable and ability.responds(event, controller)
        ]
        while abilities:
            abilities = [
                (ability, event)
                for ability, event in abilities
                if ability.is_usable and ability.responds(event, controller)
            ]
            events = dict(abilities)
            if self.auto_order:
                ability, event = abilities.pop(0)
            else:
                options = []
                if all(ability.is_optional for ability, _ in abilities):
                    options.append(SelectionInput(None))
                options.extend((SelectionInput(ability) for ability, _ in abilities))
                if len(options) == 1:
                    input = options[0]
                else:
                    input = yield State(controller or self.engine.turn_player, options, hint='Select an ability to activate')
                if input.selection:
                    ability = input.selection
                    event = events[input.selection]
                    abilities.remove((ability, event))
                else:
                    return
            yield from self.resolve(ability, event, controller)

    def resolve_preemptives(self, event: Event, controller: Player) -> StateMachine:
        abilities = [
            (ability, event)
            for ability in self._triggers(controller)
            if ability.type & event.type == event.type
            if ability.responds(event, controller)
            if ability.is_preemptive
        ]
        yield from self.resolve_multiple(abilities, controller)

    def resolve_immediates(self, event: Event, controller: Player) -> StateMachine:
        abilities = [
            (ability, event)
            for ability in self._triggers(controller)
            if ability.type & event.type == event.type
            if ability.responds(event, controller)
            if ability.is_immediate
        ]
        yield from self.resolve_multiple(abilities, controller)

    def resolve_pending(self, controller: Player) -> StateMachine:
        pending = list(self.pending[controller])
        self.pending[controller].clear()
        yield from self.resolve_multiple(pending, controller)

    def pre_event(self, event: Event) -> StateMachine:
        if not self.enabled:
            return

        self.mark_pending(event)
        for player in self.players:
            yield from self.resolve_preemptives(event, player)

    def post_event(self, event: Event) -> StateMachine:
        if not self.enabled:
            return

        for player in self.players:
            yield from self.resolve_immediates(event, player)

        if not event.parent:
            for player in self.players:
                yield from self.resolve_pending(player)
