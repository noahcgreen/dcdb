import itertools

import lua
import lua.aux as luaL

from dcdb.event.types import *

from .libs import *


def is_indexable(state, n):
    top = lua.gettop(state)
    if lua.istable(state, n):
        return True
    if not lua.isuserdata(state, n):
        return False
    if not lua.getmetatable(state, n):
        return False
    lua.getfield(state, -1, b'__index')
    has_index = not lua.isnil(state, -1)
    lua.settop(state, top)
    return has_index


@handlelib.method('release')
def handle_release(state):
    handle = handlelib.check(state, 1)
    if not handle:
        return 0
    handle.release()
    handle.card.handles.remove(handle)
    return 0


@handlelib.method('move')
def handle_move(state):
    handle = handlelib.check(state, 1)

    if pilelib.match(state, 2):
        destination = pilelib.check(state, 2)
    elif locationlib.match(state, 2):
        destination = locationlib.check(state, 2)
    else:
        return luaL.argerror(state, 2, b'Expected Pile or Location')

    if lua.isnoneornil(state, 3):
        visibility = set()
    elif is_indexable(state, 3):
        visibility = set()
        for i in itertools.count(1):
            lua.geti(state, 3, i)
            if lua.isnil(state, -1):
                lua.pop(state, 1)
                break
            elif not playerlib.match(state, -1):
                return luaL.argerror(state, 3, b'Values must be Players')
            player = playerlib.check(state, -1)
            visibility.add(player)
            lua.pop(state, 1)
    else:
        return luaL.argerror(state, 3, b'Expected array of Players')

    if handle.check_release():
        @lua.KFunction
        def continuation(state, status, context):
            lua.pushboolean(state, True)
            return 1

        move = MoveEvent(handle.card._engine, handle.card, destination, visibility=visibility)
        sm = handle.card._engine.events.dispatch(move)
        statemachinelib.create(state, sm)
        return lua.yieldk(state, 1, 0, continuation)
    else:
        lua.pushboolean(state, False)
        return 1


@handlelib.method('destroy')
def handle_destroy(state):
    handle = handlelib.check(state, 1)
    if lua.isnoneornil(state, 2):
        destroyer = None
    else:
        destroyer = playerlib.check(state, 2)

    if handle.check_release():
        @lua.KFunction
        def continuation(state, status, context):
            lua.pushboolean(state, True)
            return 1

        destroy = DestroyEvent(handle.card._engine, handle.card, destroyer)
        sm = handle.card._engine.events.dispatch(destroy)
        statemachinelib.create(state, sm)
        return lua.yieldk(state, 1, 0, continuation)
    else:
        lua.pushboolean(state, False)
        return 1


@handlelib.method('discard')
def handle_discard(state):
    handle = handlelib.check(state, 1)
    if lua.isnoneornil(state, 2):
        discarder = None
    else:
        discarder = playerlib.check(state, 2)

    if handle.check_release():
        @lua.KFunction
        def continuation(state, status, context):
            lua.pushboolean(state, True)
            return 1

        discard = DiscardEvent(handle.card._engine, handle.card)
        sm = handle.card._engine.events.dispatch(discard)
        statemachinelib.create(state, sm)
        return lua.yieldk(state, 1, 0, continuation)
    else:
        lua.pushboolean(state, False)
        return 1


@handlelib.method('play')
def handle_play(state):
    handle = handlelib.check(state, 1)
    player = playerlib.check(state, 2)

    if handle.check_release():
        @lua.KFunction
        def continuation(state, status, context):
            lua.pushboolean(state, True)
            return 1

        play = PlayEvent(handle.card._engine, player, handle.card)
        sm = handle.card._engine.events.dispatch(play)
        statemachinelib.create(state, sm)
        return lua.yieldk(state, 1, 0, continuation)
    else:
        lua.pushboolean(state, False)
        return 1


@handlelib.method('gain')
def handle_gain(state):
    handle = handlelib.check(state, 1)
    player = playerlib.check(state, 2)
    if lua.isnoneornil(state, 3):
        destination = player.discard
    elif pilelib.match(state, 3):
        destination = pilelib.check(state, 3)
    elif locationlib.match(state, 3):
        destination = locationlib.check(state, 3)
    else:
        return luaL.argerror(state, 3, b'Expected Pile or Location')

    if handle.check_release():
        @lua.KFunction
        def continuation(state, status, context):
            lua.pushboolean(state, True)
            return 1

        gain = GainEvent(handle.card._engine, handle.card, player, destination)
        sm = handle.card._engine.events.dispatch(gain)
        statemachinelib.create(state, sm)
        return lua.yieldk(state, 1, 0, continuation)
    else:
        lua.pushboolean(state, False)
        return 1


@handlelib.method('reveal')
def handle_reveal(state):
    handle = handlelib.check(state, 1)
    if is_indexable(state, 2):
        players = []
        for i in itertools.count(1):
            lua.geti(state, 2, i)
            if lua.isnil(state, -1):
                lua.pop(state, 1)
                break
            elif not playerlib.match(state, -1):
                return luaL.argerror(state, 2, b'Values must be Players')
            else:
                player = playerlib.check(state, -1)
                players.append(player)
                lua.pop(state, 1)
    elif lua.isnoneornil(state, 2):
        players = None
    else:
        return luaL.argerror(state, 2, b'Expected array of Players')
    return 0
