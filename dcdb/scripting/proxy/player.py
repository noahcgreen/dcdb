import ctypes as c
import itertools

import lua
import lua.aux as luaL

from dcdb.input import SelectionInput, State
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


def pull_value(state, n):
    if lua.isuserdata(state, n):
        ud_ptr = lua.touserdata(state, n)
        pyobj_ptr = c.cast(ud_ptr, c.POINTER(c.py_object))
        return pyobj_ptr.contents.value
    elif lua.isinteger(state, n):
        return lua.tointeger(state, n)
    elif lua.isnumber(state, n):
        return lua.tonumber(state, n)
    elif lua.isboolean(state, n):
        return lua.toboolean(state, n)
    elif lua.isstring(state, n):
        return lua.tostring(state, n).decode('utf-8')
    elif lua.isnil(state, n):
        return None
    raise ValueError('Non-convertible value')


def push_array(state, a, push_value):
    lua.createtable(state, len(a), 0)
    for i, x in enumerate(a, 1):
        push_value(state, x)
        lua.seti(state, -2, i)


@playerlib.property('hand')
def player_hand(state):
    player = playerlib.check(state, 1)
    pilelib.create(state, player.hand)
    return 1


@playerlib.property('deck')
def player_deck(state):
    player = playerlib.check(state, 1)
    pilelib.create(state, player.deck)
    return 1


@playerlib.property('in_play')
def player_in_play(state):
    player = playerlib.check(state, 1)
    pilelib.create(state, player.in_play)
    return 1


@playerlib.property('discard')
def player_discard(state):
    player = playerlib.check(state, 1)
    pilelib.create(state, player.discard)
    return 1


@playerlib.property('over_character')
def player_over_character(state):
    player = playerlib.check(state, 1)
    pilelib.create(state, player.over_character)
    return 1


@playerlib.property('under_character')
def player_under_character(state):
    player = playerlib.check(state, 1)
    pilelib.create(state, player.under_character)
    return 1


@playerlib.property('controlled')
def player_controlled(state):
    player = playerlib.check(state, 1)
    push_array(state, player.controlled, cardlib.create)
    return 1


@playerlib.property('foes')
def player_foes(state):
    player = playerlib.check(state, 1)
    push_array(state, player.foes, playerlib.create)
    return 1


@playerlib.property('characters')
def player_characters(state):
    player = playerlib.check(state, 1)
    push_array(state, player.characters, characterlib.create)
    return 1


@playerlib.method('select')
def player_select(state):
    player = playerlib.check(state, 1)
    if not is_indexable(state, 2):
        return luaL.argerror(state, 2, b'Expected array of options')
    options = []
    refs = []
    for i in itertools.count(1):
        lua.geti(state, 2, i)
        if lua.isnil(state, -1):
            lua.pop(state, 1)
            break
        else:
            ref = luaL.ref(state, lua.REGISTRYINDEX)
            refs.append(ref)
            lua.rawgeti(state, lua.REGISTRYINDEX, ref)
            option = pull_value(state, -1)
            options.append(option)
            lua.pop(state, 1)
    optional = lua.toboolean(state, 3)
    if lua.isnoneornil(state, 4):
        hint = None
    else:
        hint = luaL.checkstring(state, 4).decode('utf-8')

    if not options:
        return 0

    inputs = []
    options_to_refs = {}
    if optional:
        inputs.insert(0, SelectionInput(None))
    for i, option in enumerate(options):
        inputs.append(SelectionInput(option))
        options_to_refs[option] = refs[i]
    if len(inputs) == 1:
        if inputs[0].selection:
            lua.rawgeti(state, lua.REGISTRYINDEX, refs[0])
        else:
            lua.pushnil(state)

        for ref in refs:
            luaL.unref(state, lua.REGISTRYINDEX, ref)

        return 1
    else:
        input: SelectionInput = None

        def get_selection():
            nonlocal input
            input = yield State(player, inputs, hint=hint)

        @lua.KFunction
        def continuation(state, status, context):
            try:
                ref = options_to_refs[input.selection]
            except KeyError:
                lua.pushnil(state)
            else:
                lua.rawgeti(state, lua.REGISTRYINDEX, ref)

            for ref in refs:
                luaL.unref(state, lua.REGISTRYINDEX, ref)

            return 1

        statemachinelib.create(state, get_selection())
        return lua.yieldk(state, 1, 0, continuation)


@playerlib.method('pay_power')
def player_pay_power(state):
    player = playerlib.check(state, 1)
    amount = luaL.checkinteger(state, 2)
    player._engine.current_turn.power -= amount
    return 0


@playerlib.method('draw')
def player_draw(state):
    player = playerlib.check(state, 1)
    amount = luaL.checkinteger(state, 2) # FIXME: Allow function?
    event = DrawEvent(player._engine, player, amount)
    sm = player._engine.events.dispatch(event)
    statemachinelib.create(state, sm)
    return lua.yield_(state, 1)
