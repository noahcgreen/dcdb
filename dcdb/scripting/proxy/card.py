import ctypes as c
import itertools
import logging

import lua
import lua.aux as luaL

from .libs import *
from ..cutil import run_coroutine
from dcdb.ability.types import ManualAbility, TriggeredAbility
from dcdb.effect.types import PassiveEffect, AlterPrice
from dcdb.event.types import *
from dcdb.types import *
from dcdb.types.card import *

logger = logging.getLogger(__name__)


@cardlib.property('location')
def card_location(state):
    card = cardlib.check(state, 1)
    locationlib.create(state, card.location)
    return 1


@cardlib.property('name')
def card_name(state):
    card = cardlib.check(state, 1)
    lua.pushstring(state, card.name.encode('utf-8'))
    return 1


@cardlib.method('has_name')
def card_has_name(state):
    card = cardlib.check(state, 1)
    name = luaL.checkstring(state, 2).decode('utf-8')
    lua.pushboolean(state, card.has_name(name))
    return 1


@cardlib.method('is_copy_of')
def card_is_copy_of(state):
    card = cardlib.check(state, 1)
    other = cardlib.check(state, 2)
    lua.pushboolean(state, card.is_copy_of(other))
    return 1


@cardlib.property('type')
def card_type(state):
    card = cardlib.check(state, 1)
    card_typelib.create(state, card.type)
    return 1


@cardlib.property('color')
def card_color(state):
    card = cardlib.check(state, 1)
    colorlib.create(state, card.color)
    return 1


@cardlib.property('cost')
def card_cost(state):
    card = cardlib.check(state, 1)
    lua.pushinteger(state, card.cost)
    return 1


@cardlib.property('vp')
def card_vp(state):
    card = cardlib.check(state, 1)
    lua.pushinteger(state, card.vp)
    return 1


@cardlib.property('owner')
def card_owner(state):
    card = cardlib.check(state, 1)
    if card.owner:
        playerlib.create(state, card.owner)
    else:
        lua.pushnil(state)
    return 1


@cardlib.method('handle')
def card_handle(state):
    card = cardlib.check(state, 1)
    handle = CardHandle(card)
    card.handles.append(handle)
    handlelib.create(state, handle)
    return 1


@cardlib.method('set_attack')
def card_set_attack(state):
    logger.debug('Setting card attack')
    card = cardlib.check(state, 1)
    logger.debug('Card: %s', card.id)
    luaL.argcheck(state, lua.istable(state, 2), 2, b'Expected table')

    if lua.getfield(state, 2, b'individual') == lua.TFUNCTION:
        logger.debug('Found individual resolution function')
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def resolve_individual(attacker, target, defended):
            logger.debug('Resolving individual attack')
            top = lua.gettop(state)
            thread = lua.newthread(state)
            lua.rawgeti(thread, lua.REGISTRYINDEX, ref)

            if attacker:
                playerlib.create(thread, attacker)
            else:
                lua.pushnil(thread)

            if target:
                playerlib.create(thread, target)
            else:
                lua.pushnil(thread)

            lua.pushboolean(thread, defended)
            yield from run_coroutine(state, thread, 3)
            lua.settop(state, top)
            logger.info('Resolved individual attack')
    else:
        lua.pop(state, 1)

        def resolve_individual(attacker, target, defended):
            yield from ()
            logger.info('No individual attack')

    if lua.getfield(state, 2, b'group') == lua.TFUNCTION:
        logger.debug('Found group resolution function')
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def resolve_group(attacker, victims, defenders):
            logger.debug('Resolving group attack')
            top = lua.gettop(state)
            thread = lua.newthread(state)
            lua.rawgeti(thread, lua.REGISTRYINDEX, ref)

            if attacker:
                playerlib.create(thread, attacker)
            else:
                lua.pushnil(thread)

            lua.createtable(thread, len(victims), 0)
            for i, victim in enumerate(victims, 1):
                playerlib.create(thread, victim)
                lua.seti(thread, -2, i)

            lua.createtable(thread, len(defenders), 0)
            for i, defender in enumerate(defenders, 1):
                playerlib.create(thread, defender)
                lua.seti(thread, -2, i)
            yield from run_coroutine(state, thread, 3)
            lua.settop(state, top)
            logger.info('Resolved group attack')
    else:
        lua.pop(state, 1)

        def resolve_group(attacker, victims, defenders):
            yield from ()
            logger.info('No group attack')

    lua.getfield(state, 2, b'unavoidable')
    unavoidable = lua.toboolean(state, -1)
    lua.pop(state, -1)

    attack = Attack(resolve_individual, resolve_group)
    attack.unavoidable = unavoidable
    card.behavior.attack = attack
    attacklib.create(state, attack)
    logger.info('Set card attack for %s', card.id)
    return 1


@cardlib.method('attack')
def card_attack(state):
    card = cardlib.check(state, 1)
    if lua.isnil(state, 2):
        attacker = None
    else:
        attacker = playerlib.check(state, 2)
    attack = attacklib.check(state, 3)
    luaL.argcheck(state, lua.istable(state, 4), 4, b'Expected table')
    targets = []
    for i in itertools.count(1):
        lua.geti(state, 4, i)
        if lua.isnil(state, -1):
            lua.pop(state, 1)
            break
        else:
            target = playerlib.check(state, -1)
            targets.append(target)
            lua.pop(state, 1)
    event = AttackEvent(card._engine, attacker, attack, targets)
    sm = card._engine.events.dispatch(event)
    statemachinelib.create(state, sm)
    return lua.yield_(state, 1)


@cardlib.method('set_constant_power')
def card_set_constant_power(state):
    logger.debug('Setting constant power')
    card = cardlib.check(state, 1)
    logger.debug('Card: %s', card.id)

    if lua.isinteger(state, 2):
        amount = lua.tointeger(state, 2)
        amount_f = lambda controller: amount
    else:
        luaL.argcheck(state, lua.isfunction(state, 2), 2, b'Expected integer or function')
        lua.pushvalue(state, 2)
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def amount_f(controller):
            lua.rawgeti(state, lua.REGISTRYINDEX, ref)
            playerlib.create(state, controller)
            lua.call(state, 1, 1)
            result = lua.tointeger(state, -1)
            lua.pop(state, 1)
            return result

    card.behavior.constant_power = amount_f
    lua.pushvalue(state, 2)  # FIXME: Should return just function, not (possibly) integer
    return 1


@cardlib.method('set_faa')
def card_set_faa(state):
    logger.debug('Setting card faa')
    card = cardlib.check(state, 1)
    logger.debug('Card: %s', card.id)

    luaL.argcheck(state, lua.istable(state, 2), 2, b'Expected table')

    if lua.getfield(state, 2, b'individual') == lua.TFUNCTION:
        logger.debug('Found individual resolution function')
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def resolve_individual(attacker, target, defended):
            logger.debug('Resolving individual attack')
            top = lua.gettop(state)
            thread = lua.newthread(state)
            lua.rawgeti(thread, lua.REGISTRYINDEX, ref)

            if target:
                playerlib.create(thread, target)
            else:
                lua.pushnil(thread)

            lua.pushboolean(thread, defended)
            yield from run_coroutine(state, thread, 2)
            lua.settop(state, top)
            logger.info('Resolved individual attack')
    else:
        lua.pop(state, 1)

        def resolve_individual(attacker, target, defended):
            yield from ()
            logger.info('No individual attack')

    if lua.getfield(state, 2, b'group') == lua.TFUNCTION:
        logger.debug('Found group resolution function')
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def resolve_group(attacker, victims, defenders):
            logger.debug('Resolving group attack')
            top = lua.gettop(state)
            thread = lua.newthread(state)
            lua.rawgeti(thread, lua.REGISTRYINDEX, ref)

            lua.createtable(thread, len(victims), 0)
            for i, victim in enumerate(victims, 1):
                playerlib.create(thread, victim)
                lua.seti(thread, -2, i)

            lua.createtable(thread, len(defenders), 0)
            for i, defender in enumerate(defenders, 1):
                playerlib.create(thread, defender)
                lua.seti(thread, -2, i)
            yield from run_coroutine(state, thread, 2)
            lua.settop(state, top)
            logger.info('Resolved group attack')
    else:
        lua.pop(state, 1)

        def resolve_group(attacker, victims, defenders):
            yield from ()
            logger.info('No group attack')

    lua.getfield(state, 2, b'unavoidable')
    unavoidable = lua.toboolean(state, -1)
    lua.pop(state, -1)

    attack = Attack(resolve_individual, resolve_group)
    attack.unavoidable = unavoidable
    card.behavior.faa = attack
    attacklib.create(state, attack)
    logger.info('Set card faa for %s', card.id)
    return 1


@cardlib.method('set_defense')
def card_set_defense(state):
    logger.debug('Setting card defense')
    card = cardlib.check(state, 1)
    logger.debug('Card: %s', card.id)
    luaL.argcheck(state, lua.istable(state, 2), 2, b'Expected table')

    if lua.getfield(state, 2, b'range') == lua.TNIL:
        range = None # FIXME?
    else:
        range = regionlib.check(state, -1)
    lua.pop(state, 1)

    if lua.getfield(state, 2, b'cost') == lua.TFUNCTION:
        cost_ref = luaL.ref(state, lua.REGISTRYINDEX)

        def cost(event, defender):
            logger.debug('Calling defense cost function')
            thread = lua.newthread(state)
            lua.rawgeti(thread, lua.REGISTRYINDEX, cost_ref)
            eventlibs[type(event)].create(thread, event)
            playerlib.create(thread, defender)
            yield from run_coroutine(state, thread, 2)
            logger.info('Completed defense cost function')
    else:
        return luaL.argerror(state, 2, b'Expected cost function')

    if lua.getfield(state, 2, b'reward') == lua.TFUNCTION:
        reward_ref = luaL.ref(state, lua.REGISTRYINDEX)

        def reward(event, defender):
            logger.debug('Calling defense reward function')
            thread = lua.newthread(state)
            lua.rawgeti(thread, lua.REGISTRYINDEX, reward_ref)
            eventlibs[type(event)].create(thread, event)
            playerlib.create(thread, defender)
            yield from run_coroutine(state, thread, 2)
            logger.info('Completed defense reward function')
    else:
        return luaL.argerror(state, 2, b'Expected reward function')

    defense = Defense(card, range, cost, reward)
    card.behavior.defense = defense
    logger.info('Set card defense for %s', card.id)
    return 0


@cardlib.method('on_play')
def card_on_play(state):
    logger.debug('Setting card on_play')
    card = cardlib.check(state, 1)
    logger.debug('Card: %s', card.id)
    luaL.argcheck(state, lua.isfunction(state, 2), 2, b'Expected function')
    lua.pushvalue(state, 2)
    ref = luaL.ref(state, lua.REGISTRYINDEX)

    def on_play(player):
        logger.debug('Calling on_play of card %s', card.id)
        thread = lua.newthread(state)
        lua.rawgeti(thread, lua.REGISTRYINDEX, ref)
        playerlib.create(thread, player)
        yield from run_coroutine(state, thread, 1)
        logger.info('Completed on_play of card %s', card.id)

    card.behavior.on_play = on_play
    logger.debug('Set card on_play for %s', card.id)
    return 0


@cardlib.method('set_star_vp')
def card_set_star_vp(state):
    card = cardlib.check(state, 1)

    if lua.isinteger(state, 2):
        amount = lua.tointeger(state, 2)
        amount_f = lambda owner: amount
    else:
        luaL.argcheck(state, lua.isfunction(state, 2), 2, b'Expected integer or function')
        lua.pushvalue(state, 2)
        ref = luaL.ref(state, lua.REGISTRYINDEX)

        def amount_f(owner):
            lua.rawgeti(state, lua.REGISTRYINDEX, ref)
            playerlib.create(state, owner)
            lua.call(state, 1, 1)
            result = lua.tointeger(state, -1)
            lua.pop(state, 1)
            return result

    card.behavior.star_vp = amount_f
    return 0


@cardlib.method('ongoing')
def card_set_ongoing(state):
    card = cardlib.check(state, 1)
    card.behavior.is_ongoing = True
    if abilitylib.match(state, 2):
        ability = abilitylib.check(state, 2)
        card.ongoing_abilities.append(ability)
    return 0


@cardlib.method('bind')
def card_bind(state):
    card = cardlib.check(state, 1)
    ability = abilitylib.check(state, 2)
    if lua.isnoneornil(state, 3):
        player = None
    else:
        player = playerlib.check(state, 3)

    if player:
        if isinstance(ability, TriggeredAbility):
            player.temp_triggers.append(ability)
        elif isinstance(ability, ManualAbility):
            player.temp_manuals.append(ability)
        elif isinstance(ability, PassiveEffect):
            player.temp_effects.append(ability)
    elif isinstance(ability, TriggeredAbility):
        card.behavior.triggers.append(ability)
    elif isinstance(ability, PassiveEffect):
        card.behavior.effects.append(ability)
    else:
        return luaL.argerror(state, 3, b'Manual abilities must be bound to a player')

    return 0


@cardlib.method('power')
def card_power(state):
    card = cardlib.check(state, 1)
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

    event = PowerEvent(card._engine, player, amount_f)
    sm = card._engine.events.dispatch(event)
    statemachinelib.create(state, sm)
    return lua.yield_(state, 1)


@cardlib.method('manual')
def card_manual(state):
    card = cardlib.check(state, 1)
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

    ability = ManualAbility(card, activate, max_uses=max_uses)
    ability.range = range
    ability.can_activate = can_activate

    abilitylib.create(state, ability)
    return 1


@cardlib.method('trigger')
def card_trigger(state):
    card = cardlib.check(state, 1)
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

    ability = TriggeredAbility(card, event_type, responds, activate, max_uses=max_uses)
    ability.range = range
    ability.is_preemptive = is_preemptive
    ability.is_immediate = is_immediate
    ability.is_optional = is_optional

    abilitylib.create(state, ability)
    return 1


@cardlib.method('alter_price')
def card_alter_price(state):
    card = cardlib.check(state, 1)
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
        lua.pushinteger(state, current)
        lua.call(state, 3, 1)
        result = lua.tointeger(state, -1)
        lua.pop(state, 1)
        return result

    ability = AlterPrice(card, applies, price, max_uses=max_uses)
    ability.range = range

    abilitylib.create(state, ability)
    return 1


@cardlib.method('is_visible_to')
def card_is_visible_to(state):
    card = cardlib.check(state, 1)
    player = playerlib.check(state, 2)

    lua.pushboolean(state, player in card.visibility)
    return 1


@cardlib.property('is_defense')
def card_is_defense(state):
    card = cardlib.check(state, 1)
    is_defense = False
    for behavior in card.behaviors:
        if behavior.defense:
            is_defense = True
            break
    lua.pushboolean(state, is_defense)
    return 1
