import functools

import lua
import lua.aux as luaL

from dcdb.event.types import *
from dcdb.types import *

from ..cutil import safe_cfunction, ScriptError
from .libs import *


def push_table(state, items, push_value):
    lua.createtable(state, len(items), 0)
    for i, item in enumerate(items, 1):
        push_value(state, item)
        lua.seti(state, -2, i)


def _event_type(eventlib, state):
    event = eventlib.check(state, 1)
    event_typelib.create(state, event.type)
    return 1


def _event_parent(eventlib, state):
    event = eventlib.check(state, 1)
    if event.parent:
        eventlibs[type(event.parent)].create(state, event.parent)
    else:
        lua.pushnil(state)
    return 1


def _event_ancestor(eventlib, state):
    event = eventlib.check(state, 1)
    event_type = event_typelib.check(state, 2)
    ancestor = event.ancestor(event_type)
    if ancestor:
        eventlibs[type(ancestor)].create(state, ancestor)
    else:
        lua.pushnil(state)
    return 1


for eventlib in eventlibs.values():
    event_type = functools.partial(_event_type, eventlib)
    event_parent = functools.partial(_event_parent, eventlib)
    event_ancestor = functools.partial(_event_ancestor, eventlib)

    eventlib.property('type')(event_type)
    eventlib.property('parent')(event_parent)
    eventlib.method('ancestor')(event_ancestor)


move_eventlib = eventlibs[MoveEvent]


@move_eventlib.property('card')
def move_card(state):
    event = move_eventlib.check(state, 1)
    cardlib.create(state, event.card)
    return 1


@move_eventlib.property('destination')
def move_destination(state):
    event = move_eventlib.check(state, 1)
    if isinstance(event.destination, Pile):
        pilelib.create(state, event.destination)
    elif isinstance(event.destination, Location):
        locationlib.create(state, event.destination)
    return 1


@move_eventlib.setter('destination')
def move_set_destination(state):
    event = move_eventlib.check(state, 1)
    if pilelib.match(state, 2):
        destination = pilelib.check(state, 2)
    elif locationlib.match(state, 2):
        destination = locationlib.check(state, 2)
    else:
        return luaL.argerror(state, 2, b'Expected Pile or Location')

    event.destination = destination
    return 0


@move_eventlib.property('origin')
def move_origin(state):
    event = move_eventlib.check(state, 1)
    locationlib.create(state, event.origin)
    return 1


reveal_eventlib = eventlibs[RevealEvent]


@reveal_eventlib.property('cards')
def reveal_cards(state):
    event = reveal_eventlib.check(state, 1)
    push_table(state, event.cards, cardlib.create)
    return 1


@reveal_eventlib.property('player')
def reveal_player(state):
    event = reveal_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


gain_eventlib = eventlibs[GainEvent]


@gain_eventlib.property('card')
def gain_card(state):
    event = gain_eventlib.check(state, 1)
    cardlib.create(state, event.card)
    return 1


@gain_eventlib.property('player')
def gain_player(state):
    event = gain_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


@gain_eventlib.property('destination')
def gain_destination(state):
    event = gain_eventlib.check(state, 1)
    if isinstance(event.destination, Pile):
        pilelib.create(state, event.destination)
    elif isinstance(event.destination, Location):
        locationlib.create(state, event.destination)
    else:
        lua.pushnil(state)
    return 1


@gain_eventlib.setter('destination')
def gain_set_destination(state):
    event = gain_eventlib.check(state, 1)
    if pilelib.match(state, 2):
        destination = pilelib.check(state, 2)
    elif locationlib.match(state, 2):
        destination = locationlib.check(state, 2)
    else:
        return luaL.argerror(state, 2, b'Expected Pile or Location')

    event.destination = destination
    return 0


buy_eventlib = eventlibs[BuyEvent]


@buy_eventlib.property('card')
def buy_card(state):
    event = buy_eventlib.check(state, 1)
    cardlib.create(state, event.card)
    return 1


@buy_eventlib.property('buyer')
def buy_buyer(state):
    event = buy_eventlib.check(state, 1)
    playerlib.create(state, event.buyer)
    return 1


destroy_eventlib = eventlibs[DestroyEvent]


@destroy_eventlib.property('card')
def destroy_card(state):
    event = destroy_eventlib.check(state, 1)
    cardlib.create(state, event.card)
    return 1


@destroy_eventlib.property('destroyer')
def destroy_destroyer(state):
    event = destroy_eventlib.check(state, 1)
    playerlib.create(state, event.destroyer)
    return 1


discard_eventlib = eventlibs[DiscardEvent]


@discard_eventlib.property('card')
def discard_card(state):
    event = discard_eventlib.check(state, 1)
    cardlib.create(state, event.card)
    return 1


discard_to_deck_eventlib = eventlibs[DiscardToDeckEvent]


@discard_to_deck_eventlib.property('player')
def d2d_player(state):
    event = discard_to_deck_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


draw_eventlib = eventlibs[DrawEvent]


@draw_eventlib.property('player')
def draw_player(state):
    event = draw_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


@draw_eventlib.property('amount')
def draw_amount(state):
    event = draw_eventlib.check(state, 1)
    lua.pushinteger(state, event.amount)
    return 1


play_eventlib = eventlibs[PlayEvent]


@play_eventlib.property('player')
def play_player(state):
    event = play_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


@play_eventlib.property('card')
def play_card(state):
    event = play_eventlib.check(state, 1)
    cardlib.create(state, event.card)
    return 1


attack_i_eventlib = eventlibs[AttackIndividualEvent]


@attack_i_eventlib.property('attacker')
def atk_i_attacker(state):
    event = attack_i_eventlib.check(state, 1)
    if event.attacker:
        playerlib.create(state, event.attacker)
    else:
        lua.pushnil(state)
    return 1


@attack_i_eventlib.property('attack')
def atk_i_attack(state):
    event = attack_i_eventlib.check(state, 1)
    attacklib.create(state, event.attack)
    return 1


@attack_i_eventlib.property('target')
def atk_i_target(state):
    event = attack_i_eventlib.check(state, 1)
    playerlib.create(state, event.target)
    return 1


@attack_i_eventlib.property('victims')
def atk_i_victims(state):
    event = attack_i_eventlib.check(state, 1)
    push_table(state, event.victims, playerlib.create)
    return 1


@attack_i_eventlib.property('defenders')
def atk_i_defenders(state):
    event = attack_i_eventlib.check(state, 1)
    push_table(state, event.defenders, playerlib.create)
    return 1


attack_g_eventlib = eventlibs[AttackGroupEvent]


@attack_g_eventlib.property('attacker')
def atk_g_attacker(state):
    event = attack_g_eventlib.check(state, 1)
    if event.attacker:
        playerlib.create(state, event.attacker)
    else:
        lua.pushnil(state)
    return 1


@attack_g_eventlib.property('attack')
def atk_g_attack(state):
    event = attack_g_eventlib.check(state, 1)
    attacklib.create(state, event.attack)
    return 1


@attack_g_eventlib.property('victims')
def atk_g_victims(state):
    event = attack_g_eventlib.check(state, 1)
    push_table(state, event.victims, playerlib.create)
    return 1


@attack_g_eventlib.property('defenders')
def atk_g_defenders(state):
    event = attack_g_eventlib.check(state, 1)
    push_table(state, event.defenders, playerlib.create)
    return 1


power_eventlib = eventlibs[PowerEvent]


@power_eventlib.property('player')
def power_player(state):
    event = power_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


@power_eventlib.property('amount')
def power_amount(state):
    event = power_eventlib.check(state, 1)
    amount = event.amount

    @safe_cfunction
    def get_power(state):
        player = playerlib.check(state, 1)
        lua.pushinteger(state, amount(player))
        return 1

    funclib.create(state, get_power)
    return 1


@power_eventlib.setter('amount')
def power_set_amount(state):
    event = power_eventlib.check(state, 1)
    luaL.argcheck(state, lua.isfunction(state, 2), 2, b'Expected function')
    lua.pushvalue(state, 2)
    ref = luaL.ref(state, lua.REGISTRYINDEX)

    def amount(player):
        lua.rawgeti(state, lua.REGISTRYINDEX, ref)
        playerlib.create(state, player)
        stat = lua.pcall(state, 1, 1, 0)
        if stat != lua.OK:
            err = lua.tostring(state, -1).decode('utf-8')
            lua.pop(state, 1)
            raise ScriptError(err)
        result = lua.tointeger(state, -1)
        lua.pop(state, 1)
        return result

    event.amount = amount
    return 0


ability_eventlib = eventlibs[AbilityEvent]


@ability_eventlib.property('owner')
def ability_owner(state):
    event = ability_eventlib.check(state, 1)
    if isinstance(event.owner, Card):
        cardlib.create(state, event.owner)
    elif isinstance(event.owner, Character):
        characterlib.create(state, event.owner)
    return 1


@ability_eventlib.property('controller')
def ability_controller(state):
    event = ability_eventlib.check(state, 1)
    playerlib.create(state, event.controller)
    return 1


turn_start_eventlib = eventlibs[TurnStartEvent]


@turn_start_eventlib.property('player')
def turn_start_player(state):
    event = turn_start_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1


turn_end_eventlib = eventlibs[TurnEndEvent]


@turn_end_eventlib.property('player')
def turn_end_player(state):
    event = turn_end_eventlib.check(state, 1)
    playerlib.create(state, event.player)
    return 1
