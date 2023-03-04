import itertools

import lua
import lua.aux as luaL

from dcdb.event.types import EventType

from .libs import *


@gamelib.property('line_up')
def game_line_up(state):
    engine = gamelib.check(state, 1)
    pilelib.create(state, engine.line_up)
    return 1


@gamelib.property('main_deck')
def game_main_deck(state):
    engine = gamelib.check(state, 1)
    pilelib.create(state, engine.main_deck)
    return 1


@gamelib.property('sv_stack')
def game_sv_stack(state):
    engine = gamelib.check(state, 1)
    pilelib.create(state, engine.sv_stack)
    return 1


@gamelib.property('destroyed')
def game_destroyed(state):
    engine = gamelib.check(state, 1)
    pilelib.create(state, engine.destroyed_pile)
    return 1


@gamelib.property('kicks')
def game_kicks(state):
    engine = gamelib.check(state, 1)
    pilelib.create(state, engine.kick_stack)
    return 1


@gamelib.property('weaknesses')
def game_weaknesses(state):
    engine = gamelib.check(state, 1)
    pilelib.create(state, engine.weakness_stack)
    return 1


@gamelib.property('is_over')
def game_is_over(state):
    engine = gamelib.check(state, 1)
    lua.pushboolean(state, engine.is_over)
    return 1


@gamelib.property('current_turn')
def game_current_turn(state):
    engine = gamelib.check(state, 1)
    turnlib.create(state, engine.current_turn)
    return 1


@gamelib.property('events')
def game_events(state):
    engine = gamelib.check(state, 1)

    def is_turn_event(event):
        return not (event.type & (EventType.TURN_START | EventType.TURN_END))

    events = list(reversed(list(itertools.takewhile(is_turn_event, reversed(engine.events.log)))))

    lua.createtable(state, len(events), 0)
    for i, event in enumerate(events, 1):
        eventlibs[type(event)].create(state, event)
        lua.seti(state, -2, i)

    return 1


@gamelib.property('players')
def game_players(state):
    engine = gamelib.check(state, 1)

    lua.createtable(state, len(engine.players), 0)
    for i, player in enumerate(engine.players, 1):
        playerlib.create(state, player)
        lua.seti(state, -2, i)

    return 1
