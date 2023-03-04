import lua
import lua.aux as luaL

from dcdb.ability.types import *
from dcdb.effect.types import *
from dcdb.event.types import *

from .libs import *
from ..cutil import run_coroutine


@characterlib.property('name')
def character_name(state):
    character = characterlib.check(state, 1)
    lua.pushstring(state, character.name)
    return 1


@characterlib.property('owner')
def character_owner(state):
    character = characterlib.check(state, 1)
    playerlib.create(state, character.owner)
    return 1


@characterlib.property('is_flipped')
def character_is_flipped(state):
    character = characterlib.check(state, 1)
    lua.pushboolean(state, character.is_flipped)
    return 1


@characterlib.method('flip_up')
def character_flip_up(state):
    character = characterlib.check(state, 1)
    character.is_flipped = False
    return 0


@characterlib.method('flip_down')
def character_flip_down(state):
    character = characterlib.check(state, 1)
    character.is_flipped = True
    return 0


@characterlib.method('bind')
def character_bind(state):
    character = characterlib.check(state, 1)
    ability = abilitylib.check(state, 2)

    if isinstance(ability, ManualAbility):
        character.manuals.append(ability)
    elif isinstance(ability, TriggeredAbility):
        character.triggers.append(ability)
    elif isinstance(ability, PassiveEffect):
        character.effects.append(ability)

    return 0


@characterlib.method('manual')
def character_manual(state):
    character = characterlib.check(state, 1)
    luaL.argcheck(state, lua.istable(state, 2), 2, b'Expected table')

    lua.getfield(state, 2, b'range')
    if lua.isnil(state, -1):
        range = None
    else:
        range = regionlib.check(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'max_uses')
    if lua.isnil(state, -1):
        max_uses = None
    else:
        max_uses = luaL.checkinteger(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'activate')
    luaL.argcheck(state, lua.isfunction(state, -1), 2, b'Expected activate function')
    activate_ref = luaL.ref(state, lua.REGISTRYINDEX)

    def activate(activator):
        thread = lua.newthread(state)
        lua.rawgeti(thread, lua.REGISTRYINDEX, activate_ref)
        playerlib.create(thread, activator)
        yield from run_coroutine(state, thread, 1)

    lua.getfield(state, 2, b'can_activate')
    luaL.argcheck(state, lua.isfunction(state, -1), 2, b'Expected can_activate function')
    can_activate_ref = luaL.ref(state, lua.REGISTRYINDEX)

    def can_activate(activator):
        lua.rawgeti(state, lua.REGISTRYINDEX, can_activate_ref)
        playerlib.create(activator)
        lua.call(state, 1, 1)
        result = lua.toboolean(state, -1)
        lua.pop(state, 1)
        return result

    ability = ManualAbility(character, activate, max_uses=max_uses)
    ability.range = range
    ability.can_activate = can_activate

    abilitylib.create(state, ability)
    return 1


@characterlib.method('trigger')
def character_trigger(state):
    character = characterlib.check(state, 1)
    luaL.argcheck(state, lua.istable(state, 2), 2, b'Expected table')

    lua.getfield(state, 2, b'range')
    if lua.isnil(state, -1):
        range = None
    else:
        range = regionlib.check(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'max_uses')
    if lua.isnil(state, -1):
        max_uses = None
    else:
        max_uses = luaL.checkinteger(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'responds')
    luaL.argcheck(state, lua.isfunction(state, -1), 2, b'Expected responds function')
    responds_ref = luaL.ref(state, lua.REGISTRYINDEX)

    def responds(event, controller):
        lua.rawgeti(state, lua.REGISTRYINDEX, responds_ref)
        eventlibs[type(event)].create(state, event)
        playerlib.create(state, controller)
        lua.call(state, 2, 1)
        result = lua.toboolean(state, -1)
        lua.pop(state, 1)
        return result

    lua.getfield(state, 2, b'activate')
    luaL.argcheck(state, lua.isfunction(state, -1), 2, b'Expected activate function')
    activate_ref = luaL.ref(state, lua.REGISTRYINDEX)

    def activate(event, controller):
        thread = lua.newthread(state)
        lua.rawgeti(thread, lua.REGISTRYINDEX, activate_ref)
        eventlibs[type(event)].create(thread, event)
        playerlib.create(thread, controller)
        yield from run_coroutine(state, thread, 2)

    lua.getfield(state, 2, b'type')
    luaL.argcheck(state, event_typelib.match(state, -1), 2, b'Expected type')
    event_type = event_typelib.check(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'preemptive')
    is_preemptive = lua.toboolean(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'immediate')
    is_immediate = lua.toboolean(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'optional')
    is_optional = lua.toboolean(state, -1)
    lua.pop(state, 1)

    ability = TriggeredAbility(character, event_type, responds, activate, max_uses=max_uses)
    ability.range = range
    ability.is_preemptive = is_preemptive
    ability.is_immediate = is_immediate
    ability.is_optional = is_optional

    abilitylib.create(state, ability)
    return 1


@characterlib.method('alter_price')
def character_alter_price(state):
    character = characterlib.check(state, 1)
    luaL.argcheck(state, lua.istable(state, 2), 2, b'Expected table')

    lua.getfield(state, 2, b'range')
    if lua.isnil(state, -1):
        range = None
    else:
        range = regionlib.check(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'max_uses')
    if lua.isnil(state, -1):
        max_uses = None
    else:
        max_uses = luaL.checkinteger(state, -1)
    lua.pop(state, 1)

    lua.getfield(state, 2, b'applies')
    luaL.argcheck(state, lua.isfunction(state, -1), 2, b'Expected applies function')
    applies_ref = luaL.ref(state, lua.REGISTRYINDEX)

    def applies(card, controller):
        lua.rawgeti(state, lua.REGISTRYINDEX, applies_ref)
        cardlib.create(state, card)
        playerlib.create(state, controller)
        lua.call(state, 2, 1)
        result = lua.toboolean(state, -1)
        lua.pop(state, 1)
        return result

    lua.getfield(state, 2, b'price')
    luaL.argcheck(state, lua.isfunction(state, -1), 2, b'Expected price function')
    price_ref = luaL.ref(state, lua.REGISTRYINDEX)

    def price(card, controller, current):
        lua.rawgeti(state, lua.REGISTRYINDEX, price_ref)
        cardlib.create(state, card)
        playerlib.create(state, controller)
        lua.pushinteger(state, price_ref)
        lua.call(state, 3, 1)
        result = lua.tointeger(state, -1)
        lua.pop(state, 1)
        return result

    ability = AlterPrice(character, applies, price, max_uses=max_uses)
    ability.range = range

    abilitylib.create(state, ability)
    return 1


@characterlib.method('power')
def character_power(state):
    character = characterlib.check(state, 1)
    player = playerlib.check(state, 2)
    if lua.isfunction(state, 3):
        lua.pushvalue(state, 3)
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def amount_f(controller):
            lua.rawgeti(state, lua.REGISTRYINDEX, ref)
            playerlib.create(state, controller)
            lua.call(state, 1, 1)
            amount = lua.tointeger(state, -1)
            lua.pop(state, 1)
            return amount
    elif lua.isinteger(state, 3):
        amount = lua.tointeger(state, 3)
        amount_f = lambda controller: amount
    else:
        return luaL.argerror(state, 3, b'Expected integer')

    event = PowerEvent(character._engine, player, amount_f)
    sm = character._engine.events.dispatch(event)
    statemachinelib.create(state, sm)
    return lua.yield_(state, 1)
