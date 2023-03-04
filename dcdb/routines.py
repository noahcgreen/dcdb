from __future__ import annotations

from abc import abstractmethod
import typing as t
from .event.types import *
from .input import *
from .observe import *
from .types.location import Region

if t.TYPE_CHECKING:
    from .engine import Engine
    from .types import *
else:
    StateMachine = t.Generator[State, Input, None]


class Routine(StateMachine):

    engine: Engine
    _generator: StateMachine

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._generator = self._run()

    @abstractmethod
    def _run(self) -> StateMachine:
        pass

    def send(self, value: Input) -> State:
        return self._generator.send(value)

    def throw(self, type, value=None, traceback=None):
        return self._generator.throw(type, value, traceback)


class ReplenishLineUp(Routine):

    def _run(self) -> StateMachine:
        amount = self.engine.LINE_UP_CAPACITY - len(self.engine.line_up)
        if amount > 0:
            cards = self.engine.main_deck[:amount]
            for card in cards:
                move = MoveEvent(self.engine, card, self.engine.line_up)
                yield from self.engine.events.dispatch(move)


class Setup(Routine):

    def _run(self) -> StateMachine:
        yield from ReplenishLineUp(self.engine)
        for player in self.engine.players:
            draw = DrawEvent(self.engine, player, 5)
            yield from self.engine.events.dispatch(draw)


class Cleanup(Routine):

    def _run(self) -> StateMachine:
        yield from self.engine.events.dispatch(GameEndEvent(self.engine))
        self.engine.abilities.enabled = False
        for player in self.engine.players:
            for card in (*player.hand, *player.in_play, *player.discard):
                yield from self.engine.events.dispatch(MoveEvent(self.engine, card, player.deck))


class Turn(Routine, Observable):

    player: Player
    power: int = ObservableProperty()
    gained_sv: t.Optional[Card]
    could_replenish: bool
    next_player: t.Optional[Player]

    def __init__(self, engine: Engine, player: Player) -> None:
        super().__init__(engine)
        super(Routine, self).__init__()
        self.player = player
        self.power = 0
        self.gained_sv = None
        self.could_replenish = True
        self.next_player = None

    @property
    def _buyable_cards(self) -> t.Iterable[Card]:
        def is_buyable(card):
            return card.price(self.player) <= self.power
        cards = list(filter(is_buyable, self.engine.line_up))
        if self.engine.kick_stack and is_buyable(self.engine.kick_stack[0]):
            cards.append(self.engine.kick_stack[0])
        if self.engine.sv_stack and is_buyable(self.engine.sv_stack[0]):
            cards.append(self.engine.sv_stack[0])
        return cards

    @property
    def _playable_cards(self) -> t.Iterable[Card]:
        return self.player.hand

    @property
    def _can_replenish_line_up(self) -> bool:
        return len(self.engine.main_deck) >= self.engine.LINE_UP_CAPACITY - len(self.engine.line_up)

    def _run(self) -> StateMachine:
        yield from self.engine.events.dispatch(TurnStartEvent(self.engine, self.player))

        while True:
            options = [EndTurnInput()]
            for card in self._buyable_cards:
                options.append(BuyInput(card))
            for card in self._playable_cards:
                options.append(PlayInput(card))
            choice = yield State(self.player, options, hint='Play your turn')

            if isinstance(choice, PlayInput):
                yield from self.engine.events.dispatch(PlayEvent(self.engine, self.player, choice.card))
            elif isinstance(choice, BuyInput):
                if choice.card.location.zone.region == Region.SV_STACK:
                    self.gained_sv = choice.card
                yield from self.engine.events.dispatch(BuyEvent(self.engine, choice.card, self.player))
            elif isinstance(choice, EndTurnInput):
                break

        for card in list(self.player.hand):
            yield from self.engine.events.dispatch(DiscardEvent(self.engine, card))
        yield from self.engine.events.dispatch(TurnEndEvent(self.engine, self.player))
        for card in list(filter(lambda c: not c.is_ongoing, self.player.in_play)):
            yield from self.engine.events.dispatch(DiscardEvent(self.engine, card))

        if self._can_replenish_line_up:
            yield from ReplenishLineUp(self.engine)
            yield from self.engine.events.dispatch(DrawEvent(self.engine, self.player, 5))
        else:
            self.could_replenish = False


class TurnLoop(Routine, Observable):

    current_turn: t.Optional[Turn] = ObservableProperty()
    log: t.List[Turn]

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        super(Routine, self).__init__()
        self.current_turn = None
        self.log = []

    def _next_player(self, turn: Turn) -> Player:
        return turn.next_player or turn.player.left_foe

    def _run(self) -> StateMachine:
        player = self.engine.players[0]
        while True:
            self.current_turn = turn = Turn(self.engine, player)
            yield from self.current_turn
            self.log.append(self.current_turn)
            self.current_turn = None

            for player in self.engine.players:
                player.temp_triggers.clear()
                player.temp_manuals.clear()
                player.temp_effects.clear()
            self.engine.abilities.reset()

            if not turn.could_replenish or not self.engine.sv_stack:
                return

            if turn.gained_sv:
                next_sv = self.engine.sv_stack[0]
                next_sv.visibility = set(self.engine.players)
                faa = next_sv.behavior.faa
                if faa:
                    players = []
                    player = turn.player.left_foe
                    for _ in range(len(self.engine.players)):
                        players.append(player)
                        player = player.left_foe
                    attack = AttackEvent(self.engine, None, faa, players)
                    yield from self.engine.events.dispatch(attack)

            player = self._next_player(turn)


class GameLoop(Routine):

    setup: Setup
    turns: TurnLoop
    cleanup: Cleanup

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.setup = Setup(self.engine)
        self.turns = TurnLoop(engine)
        self.cleanup = Cleanup(engine)

    def _run(self) -> StateMachine:
        yield from self.setup
        self.engine.abilities.enabled = True
        yield from self.turns
        yield from self.cleanup
