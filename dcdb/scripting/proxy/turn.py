import lua
import lua.aux as luaL

from .libs import *


@turnlib.property('power')
def turn_power(state):
    turn = turnlib.check(state, 1)
    lua.pushinteger(state, turn.power)
    return 1


@turnlib.setter('power')
def turn_set_power(state):
    turn = turnlib.check(state, 1)
    amount = luaL.checkinteger(state, 2)
    turn.power = amount
    return 0


@turnlib.property('player')
def turn_player(state):
    turn = turnlib.check(state, 1)
    playerlib.create(state, turn.player)
    return 1
