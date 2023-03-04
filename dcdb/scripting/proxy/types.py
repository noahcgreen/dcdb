import ctypes as c
import functools

import lua
import lua.aux as luaL

from .libs import *
from dcdb.event.types import *
from dcdb.types import *


@pilelib.metamethod('__len')
def pile_length(state):
    pile = pilelib.check(state, 1)
    lua.pushinteger(state, len(pile))
    return 1


@pilelib.index
def pile_get_index(state):
    pile = pilelib.check(state, 1)
    index = luaL.checkinteger(state, 2)

    @lua.KFunction
    def continuation(state, status, context):
        if pile and 0 < index <= len(pile):
            cardlib.create(state, pile[index - 1])
        else:
            lua.pushnil(state)
        return 1

    if pile.zone.region == Region.DECK and len(pile) < index and 0 < index <= len(pile) + len(pile.zone.player.discard):
        shuffle = DiscardToDeckEvent(pile._engine, pile.zone.player)
        sm = pile._engine.events.dispatch(shuffle)
        statemachinelib.create(state, sm)
        return lua.yieldk(state, 1, 0, continuation)
    else:
        return continuation(state, 0, c.cast(None, lua.KContext))


def _flag_band(flaglib, state):
    f1 = flaglib.check(state, 1)
    f2 = flaglib.check(state, 2)
    flaglib.create(state, f1 & f2)
    return 1


def _flag_bor(flaglib, state):
    f1 = flaglib.check(state, 1)
    f2 = flaglib.check(state, 2)
    flaglib.create(state, f1 | f2)
    return 1


def _flag_bxor(flaglib, state):
    f1 = flaglib.check(state, 1)
    f2 = flaglib.check(state, 2)
    flaglib.create(state, f1 ^ f2)
    return 1


def _flag_bnot(flaglib, state):
    f = flaglib.check(state, 1)
    flaglib.create(state, ~f)
    return 1


for flaglib in [card_typelib, colorlib, event_typelib, regionlib]:
    band = functools.partial(_flag_band, flaglib)
    bor = functools.partial(_flag_bor, flaglib)
    bxor = functools.partial(_flag_bxor, flaglib)
    bnot = functools.partial(_flag_bnot, flaglib)

    flaglib.metamethod('__band')(band)
    flaglib.metamethod('__bor')(bor)
    flaglib.metamethod('__bxor')(bxor)
    flaglib.metamethod('__bnot')(bnot)


@zonelib.property('region')
def zone_region(state):
    zone = zonelib.check(state, 1)
    regionlib.create(state, zone.region)
    return 1


@zonelib.property('player')
def zone_player(state):
    zone = zonelib.check(state, 1)
    if zone.player:
        playerlib.create(state, zone.player)
    else:
        lua.pushnil(state)
    return 1


@zone_typelib.metamethod('__call')
def zone_type_new(state):
    zone_typelib.check(state, 1)
    region = regionlib.check(state, 2)
    if lua.isnoneornil(state, 3):
        player = None
    else:
        player = playerlib.check(state, 3)
    if lua.isnoneornil(state, 4):
        card = None
    else:
        card = cardlib.check(state, 4)
    zonelib.create(state, Zone(region, player, card))
    return 1


@locationlib.property('zone')
def location_zone(state):
    location = locationlib.check(state, 1)
    zonelib.create(state, location.zone)
    return 1


@locationlib.property('index')
def location_index(state):
    location = locationlib.check(state, 1)
    lua.pushinteger(state, location.index + 1)
    return 1


@location_typelib.metamethod('__call')
def location_type_new(state):
    location_typelib.check(state, 1)
    zone = zonelib.check(state, 2)
    index = luaL.checkinteger(state, 3)

    locationlib.create(state, Location(zone, index - 1))
    return 1


def _get_flag(flag_typelib, flaglib, flag, state):
    flag_typelib.check(state, 1)
    flaglib.create(state, flag)
    return 1


for flag_type, flag_typelib, flaglib in [
    (CardType, card_type_typelib, card_typelib),
    (Color, color_typelib, colorlib),
    (Region, region_typelib, regionlib),
    (EventType, event_type_typelib, event_typelib)
]:
    for flag in flag_type:
        get_flag = functools.partial(_get_flag, flag_typelib, flaglib, flag)
        flag_typelib.property(flag.name)(get_flag)
